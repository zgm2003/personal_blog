---
title: 文件上传模块
published: 2026-01-14T10:00:00Z
description: 多云存储驱动、临时凭证、前端直传的完整实现
tags: [系统, 上传, COS, OSS]
category: 系统管理
draft: false
---

# 模块概述

文件上传是后台系统的基础功能。本模块实现了：

- 多云存储驱动（腾讯云 COS、阿里云 OSS）
- 临时凭证机制，前端直传云存储
- 上传规则配置（文件类型、大小限制）
- 驱动 + 规则组合管理

## 架构设计

```
前端请求上传凭证
    ↓
后端生成临时 STS Token
    ↓
前端直传云存储
    ↓
返回文件 URL
```

**优势**：文件不经过服务器，减轻带宽压力，上传速度更快。

---

## 后端实现

### 目录结构

```
app/module/
├── UploadModule.php              # 获取上传凭证
└── System/
    ├── UploadDriverModule.php    # 驱动管理（COS/OSS配置）
    ├── UploadRuleModule.php      # 规则管理（类型/大小限制）
    └── UploadSettingModule.php   # 设置管理（驱动+规则组合）
```

### 获取上传凭证

```php
class UploadModule extends BaseModule
{
    private $allowedFolders = [
        'avatar', 'upload', 'file', 'image', 'article', 'ai_chat_images'
    ];

    public function getUploadToken($request)
    {
        $folder = trim((string)$request->input('folderName', ''));

        // 安全校验：防止目录穿越
        if (!in_array($folder, $this->allowedFolders, true) 
            || str_contains($folder, '..')) {
            return self::error('folderName 非法', 400);
        }

        $setting = (new UploadSettingDep())->getActive();
        if (!$setting) {
            return self::error('未配置有效的上传设置', 500);
        }

        // 根据驱动类型获取临时凭证
        $data = match($setting['driver']) {
            'cos' => $this->getCosToken($setting, $folder),
            'oss' => $this->getOssToken($setting, $folder),
            default => throw new \Exception('不支持的驱动类型'),
        };

        // 附加上传规则
        $data['rule'] = [
            'maxSize' => (int)$setting['max_size_mb'],
            'imageExts' => json_decode($setting['image_exts'] ?? '[]'),
            'fileExts' => json_decode($setting['file_exts'] ?? '[]'),
        ];

        return self::success($data);
    }
}
```

### 腾讯云 COS 临时凭证

```php
private function getCosToken($setting, $folder)
{
    $cred = new Credential($setting['secret_id'], $setting['secret_key']);
    $client = new StsClient($cred, $setting['region'], new ClientProfile());

    // 最小权限策略：只允许上传到指定目录
    $policy = [
        'version' => '2.0',
        'statement' => [[
            'action' => ['cos:PutObject', 'cos:PostObject'],
            'effect' => 'allow',
            'resource' => [
                "qcs::cos:{$setting['region']}:uid/{$setting['appid']}:{$setting['bucket']}/{$folder}/*"
            ],
        ]],
    ];

    $req = new GetFederationTokenRequest();
    $req->fromJsonString(json_encode([
        'DurationSeconds' => 1800,  // 30分钟有效期
        'Name' => 'upload-' . date('YmdHis'),
        'Policy' => json_encode($policy),
    ]));

    $response = $client->GetFederationToken($req);

    return [
        'provider' => 'cos',
        'credentials' => [
            'tmpSecretId'  => $response->Credentials->TmpSecretId,
            'tmpSecretKey' => $response->Credentials->TmpSecretKey,
            'sessionToken' => $response->Credentials->Token,
        ],
        'expiredTime' => (int)$response->ExpiredTime,
        'bucket' => $setting['bucket'],
        'region' => $setting['region'],
        'uploadPath' => "{$folder}/",
    ];
}
```

### 阿里云 OSS 临时凭证

```php
private function getOssToken($setting, $folder)
{
    AlibabaCloud::accessKeyClient($setting['secret_id'], $setting['secret_key'])
        ->regionId($setting['region'])
        ->asDefaultClient();

    $policy = [
        'Version' => '1',
        'Statement' => [[
            'Effect' => 'Allow',
            'Action' => ['oss:PutObject', 'oss:PostObject'],
            'Resource' => ["acs:oss:*:*:{$setting['bucket']}/{$folder}/*"],
        ]],
    ];

    $res = \AlibabaCloud\Sts\Sts::v20150401()
        ->assumeRole()
        ->withRoleArn($setting['role_arn'])
        ->withRoleSessionName('oss-upload-' . date('YmdHis'))
        ->withDurationSeconds(1800)
        ->withPolicy(json_encode($policy))
        ->request();

    $cred = $res->get('Credentials');

    return [
        'provider' => 'oss',
        'credentials' => [
            'tmpSecretId'  => $cred['AccessKeyId'],
            'tmpSecretKey' => $cred['AccessKeySecret'],
            'sessionToken' => $cred['SecurityToken'],
        ],
        'bucket' => $setting['bucket'],
        'region' => $setting['region'],
        'uploadPath' => "{$folder}/",
    ];
}
```

---

## 前端实现

### 上传组件封装

```typescript
// composables/useUpload.ts
export function useUpload() {
  const uploading = ref(false)
  
  const getToken = async (folderName: string) => {
    const res = await UploadApi.getToken({ folderName })
    return res.data
  }
  
  const upload = async (file: File, folder: string) => {
    uploading.value = true
    
    try {
      const token = await getToken(folder)
      
      // 校验文件
      validateFile(file, token.rule)
      
      // 根据云服务商选择上传方式
      if (token.provider === 'cos') {
        return await uploadToCos(file, token)
      } else {
        return await uploadToOss(file, token)
      }
    } finally {
      uploading.value = false
    }
  }
  
  return { uploading, upload }
}
```

### COS 直传

```typescript
async function uploadToCos(file: File, token: UploadToken) {
  const cos = new COS({
    getAuthorization: (_, callback) => {
      callback({
        TmpSecretId: token.credentials.tmpSecretId,
        TmpSecretKey: token.credentials.tmpSecretKey,
        SecurityToken: token.credentials.sessionToken,
        StartTime: token.startTime,
        ExpiredTime: token.expiredTime,
      })
    }
  })
  
  const key = `${token.uploadPath}${Date.now()}_${file.name}`
  
  return new Promise((resolve, reject) => {
    cos.uploadFile({
      Bucket: token.bucket,
      Region: token.region,
      Key: key,
      Body: file,
      onProgress: (info) => {
        console.log('上传进度:', Math.round(info.percent * 100) + '%')
      }
    }, (err, data) => {
      if (err) reject(err)
      else resolve(`https://${token.bucket}.cos.${token.region}.myqcloud.com/${key}`)
    })
  })
}
```

### 文件校验

```typescript
function validateFile(file: File, rule: UploadRule) {
  // 大小校验
  const maxBytes = rule.maxSize * 1024 * 1024
  if (file.size > maxBytes) {
    throw new Error(`文件大小不能超过 ${rule.maxSize}MB`)
  }
  
  // 类型校验
  const ext = file.name.split('.').pop()?.toLowerCase()
  const isImage = file.type.startsWith('image/')
  const allowedExts = isImage ? rule.imageExts : rule.fileExts
  
  if (!allowedExts.includes(ext)) {
    throw new Error(`不支持的文件类型: ${ext}`)
  }
}
```

---

## 管理后台

### 驱动配置页面

配置云存储账号信息：

| 字段 | COS | OSS |
|------|-----|-----|
| SecretId | ✅ | ✅ |
| SecretKey | ✅ | ✅ |
| Bucket | ✅ | ✅ |
| Region | ✅ | ✅ |
| AppId | ✅ | - |
| RoleArn | - | ✅ |

### 规则配置页面

配置上传限制：

- 最大文件大小（MB）
- 允许的图片格式（jpg, png, gif, webp...）
- 允许的文件格式（pdf, doc, xlsx...）

### 设置管理

将驱动和规则组合，启用一个作为当前生效配置。

---

## 安全考虑

1. **最小权限原则**：临时凭证只授予 PutObject 权限，且限定目录
2. **目录白名单**：防止用户上传到任意目录
3. **路径穿越防护**：检测 `..` 等危险字符
4. **凭证有效期**：30 分钟过期，降低泄露风险
5. **前端校验 + 后端校验**：双重保障

## 扩展方向

- 支持更多云存储（七牛、又拍云）
- 图片处理（压缩、裁剪、水印）
- 断点续传
- 上传进度回调
