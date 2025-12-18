package com.omniagent.sdk.model;

import lombok.Data;
import lombok.AllArgsConstructor;

/**
 * Chat 响应
 */
@Data
@AllArgsConstructor
public class ChatResponse {
    private String content;
    private String finishReason;
    
    public static ChatResponse fromProto(OmniAgentProto.ChatResponse proto) {
        return new ChatResponse(
            proto.getContent(),
            proto.getFinishReason().isEmpty() ? null : proto.getFinishReason()
        );
    }
}
