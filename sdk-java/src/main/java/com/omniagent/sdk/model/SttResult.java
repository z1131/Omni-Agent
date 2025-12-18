package com.omniagent.sdk.model;

import lombok.Data;
import lombok.AllArgsConstructor;

/**
 * STT 识别结果
 */
@Data
@AllArgsConstructor
public class SttResult {
    private String text;
    private boolean isFinal;
    private float confidence;
    private long startTimeMs;
    private long endTimeMs;
    
    public long getDurationMs() {
        return endTimeMs - startTimeMs;
    }
    
    public static SttResult fromProto(OmniAgentProto.SttResult proto) {
        return new SttResult(
            proto.getText(),
            proto.getIsFinal(),
            proto.getConfidence(),
            proto.getStartTimeMs(),
            proto.getEndTimeMs()
        );
    }
}
