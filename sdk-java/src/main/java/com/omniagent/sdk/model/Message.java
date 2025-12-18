package com.omniagent.sdk.model;

import lombok.Data;
import lombok.AllArgsConstructor;

/**
 * 对话消息
 */
@Data
@AllArgsConstructor
public class Message {
    private String role;
    private String content;
    
    public static Message user(String content) {
        return new Message("user", content);
    }
    
    public static Message assistant(String content) {
        return new Message("assistant", content);
    }
    
    public static Message system(String content) {
        return new Message("system", content);
    }
    
    public OmniAgentProto.Message toProto() {
        return OmniAgentProto.Message.newBuilder()
            .setRole(role)
            .setContent(content)
            .build();
    }
}
