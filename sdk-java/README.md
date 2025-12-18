# Omni-Agent Java SDK

通用智能体 Java 客户端库。

## 安装

### Maven

```xml
<dependency>
    <groupId>com.omniagent</groupId>
    <artifactId>omni-agent-sdk</artifactId>
    <version>0.1.0</version>
</dependency>
```

### Gradle

```groovy
implementation 'com.omniagent:omni-agent-sdk:0.1.0'
```

## 快速开始

```java
import com.omniagent.sdk.*;
import com.omniagent.sdk.model.*;

// 创建客户端
OmniAgentClient client = OmniAgentClient.builder()
    .target("localhost:50051")
    .build();

// 创建会话
Session session = client.createSession(SessionConfig.builder()
    .model("qwen-plus")
    .systemPrompt("你是专业助手")
    .build());

// 简单对话
String response = session.chat("你好");
System.out.println(response);

// 流式对话
session.chatStream("讲个故事", chunk -> System.out.print(chunk));
System.out.println();

// 关闭
session.close();
client.shutdown();
```

## 功能特性

### 会话管理

```java
// 创建会话
Session session = client.createSession(SessionConfig.builder()
    .model("qwen-turbo")
    .systemPrompt("你是助手")
    .temperature(0.7f)
    .sttModel("paraformer-realtime-v2")
    .language("zh-CN")
    .build());

// 获取已有会话
Session session = client.getSession("session_id");

// 关闭会话
session.close();
```

### 对话

```java
// 简单对话（自动维护历史）
String response = session.chat("你好");
response = session.chat("继续上面的话题");

// 不记录历史
response = session.chat("临时问题", false);

// 流式对话
session.chatStream("讲个故事", chunk -> System.out.print(chunk));

// 清空历史
session.clearHistory();

// 设置系统提示词
session.setSystemPrompt("你现在是翻译助手");
```

### 统一多模态接口（推荐）

```java
import com.omniagent.sdk.model.*;

// 非流式多模态处理
ProcessingConfig config = ProcessingConfig.builder()
    .llmModel("qwen-plus")
    .systemPrompt("你是专业面试官")
    .language("zh-CN")
    .build();

// 纯文本
String response = client.processText("session_id", "你好", config);

// 音频输入
String response = client.processAudio("session_id", audioBytes, config);

// 多模态组合
List<MultiModalInput> inputs = List.of(
    MultiModalInput.ofText("请根据以下音频内容回答"),
    MultiModalInput.ofAudio(audioBytes)
);
MultiModalResponse response = client.process("session_id", inputs, config);
System.out.println(response.getTextContent());
System.out.println("STT结果: " + response.getMetadata().getTranscribedText());
```

### 流式多模态处理

```java
// 创建流式处理
MultiModalStream stream = client.processStream(
    "session_id",
    config,
    stt -> System.out.println("识别: " + stt),    // STT 中间结果
    llm -> System.out.print(llm),                  // LLM 增量输出
    () -> System.out.println("\n完成"),            // 完成回调
    err -> err.printStackTrace()                   // 错误回调
);

// 发送音频流
stream.sendAudio(audioChunk1);
stream.sendAudio(audioChunk2);
stream.sendAudio(audioChunk3);

// 结束音频，开始生成回复
stream.endAudio();
```

### 语音识别 (STT)

```java
// 单次识别
String text = session.transcribe(audioBytes);

// 流式识别
StreamObserver<byte[]> audioSender = session.transcribeStream(
    result -> {
        if (result.isFinal()) {
            System.out.println("最终: " + result.getText());
        } else {
            System.out.println("中间: " + result.getText());
        }
    },
    error -> error.printStackTrace(),
    () -> System.out.println("完成")
);

// 发送音频数据
audioSender.onNext(audioChunk1);
audioSender.onNext(audioChunk2);
audioSender.onCompleted();
```

## 异常处理

```java
import com.omniagent.sdk.exception.*;

try {
    String response = session.chat("你好");
} catch (SessionNotFoundException e) {
    System.out.println("会话不存在: " + e.getSessionId());
} catch (ConnectionException e) {
    System.out.println("连接错误: " + e.getMessage());
} catch (TimeoutException e) {
    System.out.println("超时: " + e.getMessage());
} catch (OmniAgentException e) {
    System.out.println("错误: " + e.getCode() + " - " + e.getMessage());
}
```

## 资源管理

```java
// try-with-resources
try (OmniAgentClient client = OmniAgentClient.builder()
        .target("localhost:50051")
        .build()) {
    
    try (Session session = client.createSession()) {
        String response = session.chat("你好");
    }
}
```

## 构建

```bash
mvn clean install
```

## License

MIT
