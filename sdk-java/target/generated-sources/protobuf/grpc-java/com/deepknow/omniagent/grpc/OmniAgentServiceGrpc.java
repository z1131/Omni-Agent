package com.deepknow.omniagent.grpc;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 * <pre>
 * Omni-Agent gRPC 服务
 * 提供统一多模态 AI 能力
 * </pre>
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.60.0)",
    comments = "Source: omni_agent.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class OmniAgentServiceGrpc {

  private OmniAgentServiceGrpc() {}

  public static final java.lang.String SERVICE_NAME = "omniagent.OmniAgentService";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<com.deepknow.omniagent.grpc.MultiModalRequest,
      com.deepknow.omniagent.grpc.MultiModalResponse> getProcessMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "Process",
      requestType = com.deepknow.omniagent.grpc.MultiModalRequest.class,
      responseType = com.deepknow.omniagent.grpc.MultiModalResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.deepknow.omniagent.grpc.MultiModalRequest,
      com.deepknow.omniagent.grpc.MultiModalResponse> getProcessMethod() {
    io.grpc.MethodDescriptor<com.deepknow.omniagent.grpc.MultiModalRequest, com.deepknow.omniagent.grpc.MultiModalResponse> getProcessMethod;
    if ((getProcessMethod = OmniAgentServiceGrpc.getProcessMethod) == null) {
      synchronized (OmniAgentServiceGrpc.class) {
        if ((getProcessMethod = OmniAgentServiceGrpc.getProcessMethod) == null) {
          OmniAgentServiceGrpc.getProcessMethod = getProcessMethod =
              io.grpc.MethodDescriptor.<com.deepknow.omniagent.grpc.MultiModalRequest, com.deepknow.omniagent.grpc.MultiModalResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "Process"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.deepknow.omniagent.grpc.MultiModalRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.deepknow.omniagent.grpc.MultiModalResponse.getDefaultInstance()))
              .setSchemaDescriptor(new OmniAgentServiceMethodDescriptorSupplier("Process"))
              .build();
        }
      }
    }
    return getProcessMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.deepknow.omniagent.grpc.MultiModalStreamRequest,
      com.deepknow.omniagent.grpc.MultiModalStreamResponse> getProcessStreamMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "ProcessStream",
      requestType = com.deepknow.omniagent.grpc.MultiModalStreamRequest.class,
      responseType = com.deepknow.omniagent.grpc.MultiModalStreamResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.BIDI_STREAMING)
  public static io.grpc.MethodDescriptor<com.deepknow.omniagent.grpc.MultiModalStreamRequest,
      com.deepknow.omniagent.grpc.MultiModalStreamResponse> getProcessStreamMethod() {
    io.grpc.MethodDescriptor<com.deepknow.omniagent.grpc.MultiModalStreamRequest, com.deepknow.omniagent.grpc.MultiModalStreamResponse> getProcessStreamMethod;
    if ((getProcessStreamMethod = OmniAgentServiceGrpc.getProcessStreamMethod) == null) {
      synchronized (OmniAgentServiceGrpc.class) {
        if ((getProcessStreamMethod = OmniAgentServiceGrpc.getProcessStreamMethod) == null) {
          OmniAgentServiceGrpc.getProcessStreamMethod = getProcessStreamMethod =
              io.grpc.MethodDescriptor.<com.deepknow.omniagent.grpc.MultiModalStreamRequest, com.deepknow.omniagent.grpc.MultiModalStreamResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.BIDI_STREAMING)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "ProcessStream"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.deepknow.omniagent.grpc.MultiModalStreamRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.deepknow.omniagent.grpc.MultiModalStreamResponse.getDefaultInstance()))
              .setSchemaDescriptor(new OmniAgentServiceMethodDescriptorSupplier("ProcessStream"))
              .build();
        }
      }
    }
    return getProcessStreamMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.deepknow.omniagent.grpc.SttRequest,
      com.deepknow.omniagent.grpc.SttResponse> getStreamSTTMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "StreamSTT",
      requestType = com.deepknow.omniagent.grpc.SttRequest.class,
      responseType = com.deepknow.omniagent.grpc.SttResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.BIDI_STREAMING)
  public static io.grpc.MethodDescriptor<com.deepknow.omniagent.grpc.SttRequest,
      com.deepknow.omniagent.grpc.SttResponse> getStreamSTTMethod() {
    io.grpc.MethodDescriptor<com.deepknow.omniagent.grpc.SttRequest, com.deepknow.omniagent.grpc.SttResponse> getStreamSTTMethod;
    if ((getStreamSTTMethod = OmniAgentServiceGrpc.getStreamSTTMethod) == null) {
      synchronized (OmniAgentServiceGrpc.class) {
        if ((getStreamSTTMethod = OmniAgentServiceGrpc.getStreamSTTMethod) == null) {
          OmniAgentServiceGrpc.getStreamSTTMethod = getStreamSTTMethod =
              io.grpc.MethodDescriptor.<com.deepknow.omniagent.grpc.SttRequest, com.deepknow.omniagent.grpc.SttResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.BIDI_STREAMING)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "StreamSTT"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.deepknow.omniagent.grpc.SttRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.deepknow.omniagent.grpc.SttResponse.getDefaultInstance()))
              .setSchemaDescriptor(new OmniAgentServiceMethodDescriptorSupplier("StreamSTT"))
              .build();
        }
      }
    }
    return getStreamSTTMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.deepknow.omniagent.grpc.ChatRequest,
      com.deepknow.omniagent.grpc.ChatResponse> getStreamChatMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "StreamChat",
      requestType = com.deepknow.omniagent.grpc.ChatRequest.class,
      responseType = com.deepknow.omniagent.grpc.ChatResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.SERVER_STREAMING)
  public static io.grpc.MethodDescriptor<com.deepknow.omniagent.grpc.ChatRequest,
      com.deepknow.omniagent.grpc.ChatResponse> getStreamChatMethod() {
    io.grpc.MethodDescriptor<com.deepknow.omniagent.grpc.ChatRequest, com.deepknow.omniagent.grpc.ChatResponse> getStreamChatMethod;
    if ((getStreamChatMethod = OmniAgentServiceGrpc.getStreamChatMethod) == null) {
      synchronized (OmniAgentServiceGrpc.class) {
        if ((getStreamChatMethod = OmniAgentServiceGrpc.getStreamChatMethod) == null) {
          OmniAgentServiceGrpc.getStreamChatMethod = getStreamChatMethod =
              io.grpc.MethodDescriptor.<com.deepknow.omniagent.grpc.ChatRequest, com.deepknow.omniagent.grpc.ChatResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.SERVER_STREAMING)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "StreamChat"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.deepknow.omniagent.grpc.ChatRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.deepknow.omniagent.grpc.ChatResponse.getDefaultInstance()))
              .setSchemaDescriptor(new OmniAgentServiceMethodDescriptorSupplier("StreamChat"))
              .build();
        }
      }
    }
    return getStreamChatMethod;
  }

  private static volatile io.grpc.MethodDescriptor<com.deepknow.omniagent.grpc.HealthRequest,
      com.deepknow.omniagent.grpc.HealthResponse> getHealthCheckMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "HealthCheck",
      requestType = com.deepknow.omniagent.grpc.HealthRequest.class,
      responseType = com.deepknow.omniagent.grpc.HealthResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<com.deepknow.omniagent.grpc.HealthRequest,
      com.deepknow.omniagent.grpc.HealthResponse> getHealthCheckMethod() {
    io.grpc.MethodDescriptor<com.deepknow.omniagent.grpc.HealthRequest, com.deepknow.omniagent.grpc.HealthResponse> getHealthCheckMethod;
    if ((getHealthCheckMethod = OmniAgentServiceGrpc.getHealthCheckMethod) == null) {
      synchronized (OmniAgentServiceGrpc.class) {
        if ((getHealthCheckMethod = OmniAgentServiceGrpc.getHealthCheckMethod) == null) {
          OmniAgentServiceGrpc.getHealthCheckMethod = getHealthCheckMethod =
              io.grpc.MethodDescriptor.<com.deepknow.omniagent.grpc.HealthRequest, com.deepknow.omniagent.grpc.HealthResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "HealthCheck"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.deepknow.omniagent.grpc.HealthRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  com.deepknow.omniagent.grpc.HealthResponse.getDefaultInstance()))
              .setSchemaDescriptor(new OmniAgentServiceMethodDescriptorSupplier("HealthCheck"))
              .build();
        }
      }
    }
    return getHealthCheckMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static OmniAgentServiceStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<OmniAgentServiceStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<OmniAgentServiceStub>() {
        @java.lang.Override
        public OmniAgentServiceStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new OmniAgentServiceStub(channel, callOptions);
        }
      };
    return OmniAgentServiceStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static OmniAgentServiceBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<OmniAgentServiceBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<OmniAgentServiceBlockingStub>() {
        @java.lang.Override
        public OmniAgentServiceBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new OmniAgentServiceBlockingStub(channel, callOptions);
        }
      };
    return OmniAgentServiceBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static OmniAgentServiceFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<OmniAgentServiceFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<OmniAgentServiceFutureStub>() {
        @java.lang.Override
        public OmniAgentServiceFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new OmniAgentServiceFutureStub(channel, callOptions);
        }
      };
    return OmniAgentServiceFutureStub.newStub(factory, channel);
  }

  /**
   * <pre>
   * Omni-Agent gRPC 服务
   * 提供统一多模态 AI 能力
   * </pre>
   */
  public interface AsyncService {

    /**
     * <pre>
     * 非流式多模态处理：支持 text + audio + image 组合输入
     * </pre>
     */
    default void process(com.deepknow.omniagent.grpc.MultiModalRequest request,
        io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.MultiModalResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getProcessMethod(), responseObserver);
    }

    /**
     * <pre>
     * 流式多模态处理：支持实时音频输入 + 流式输出
     * </pre>
     */
    default io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.MultiModalStreamRequest> processStream(
        io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.MultiModalStreamResponse> responseObserver) {
      return io.grpc.stub.ServerCalls.asyncUnimplementedStreamingCall(getProcessStreamMethod(), responseObserver);
    }

    /**
     * <pre>
     * STT 双向流：客户端发送音频帧，服务端返回识别结果
     * </pre>
     */
    default io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.SttRequest> streamSTT(
        io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.SttResponse> responseObserver) {
      return io.grpc.stub.ServerCalls.asyncUnimplementedStreamingCall(getStreamSTTMethod(), responseObserver);
    }

    /**
     * <pre>
     * LLM 流式调用：客户端发送问题，服务端流式返回答案
     * </pre>
     */
    default void streamChat(com.deepknow.omniagent.grpc.ChatRequest request,
        io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.ChatResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getStreamChatMethod(), responseObserver);
    }

    /**
     * <pre>
     * 健康检查
     * </pre>
     */
    default void healthCheck(com.deepknow.omniagent.grpc.HealthRequest request,
        io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.HealthResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getHealthCheckMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service OmniAgentService.
   * <pre>
   * Omni-Agent gRPC 服务
   * 提供统一多模态 AI 能力
   * </pre>
   */
  public static abstract class OmniAgentServiceImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return OmniAgentServiceGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service OmniAgentService.
   * <pre>
   * Omni-Agent gRPC 服务
   * 提供统一多模态 AI 能力
   * </pre>
   */
  public static final class OmniAgentServiceStub
      extends io.grpc.stub.AbstractAsyncStub<OmniAgentServiceStub> {
    private OmniAgentServiceStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected OmniAgentServiceStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new OmniAgentServiceStub(channel, callOptions);
    }

    /**
     * <pre>
     * 非流式多模态处理：支持 text + audio + image 组合输入
     * </pre>
     */
    public void process(com.deepknow.omniagent.grpc.MultiModalRequest request,
        io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.MultiModalResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getProcessMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * 流式多模态处理：支持实时音频输入 + 流式输出
     * </pre>
     */
    public io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.MultiModalStreamRequest> processStream(
        io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.MultiModalStreamResponse> responseObserver) {
      return io.grpc.stub.ClientCalls.asyncBidiStreamingCall(
          getChannel().newCall(getProcessStreamMethod(), getCallOptions()), responseObserver);
    }

    /**
     * <pre>
     * STT 双向流：客户端发送音频帧，服务端返回识别结果
     * </pre>
     */
    public io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.SttRequest> streamSTT(
        io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.SttResponse> responseObserver) {
      return io.grpc.stub.ClientCalls.asyncBidiStreamingCall(
          getChannel().newCall(getStreamSTTMethod(), getCallOptions()), responseObserver);
    }

    /**
     * <pre>
     * LLM 流式调用：客户端发送问题，服务端流式返回答案
     * </pre>
     */
    public void streamChat(com.deepknow.omniagent.grpc.ChatRequest request,
        io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.ChatResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncServerStreamingCall(
          getChannel().newCall(getStreamChatMethod(), getCallOptions()), request, responseObserver);
    }

    /**
     * <pre>
     * 健康检查
     * </pre>
     */
    public void healthCheck(com.deepknow.omniagent.grpc.HealthRequest request,
        io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.HealthResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getHealthCheckMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service OmniAgentService.
   * <pre>
   * Omni-Agent gRPC 服务
   * 提供统一多模态 AI 能力
   * </pre>
   */
  public static final class OmniAgentServiceBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<OmniAgentServiceBlockingStub> {
    private OmniAgentServiceBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected OmniAgentServiceBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new OmniAgentServiceBlockingStub(channel, callOptions);
    }

    /**
     * <pre>
     * 非流式多模态处理：支持 text + audio + image 组合输入
     * </pre>
     */
    public com.deepknow.omniagent.grpc.MultiModalResponse process(com.deepknow.omniagent.grpc.MultiModalRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getProcessMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * LLM 流式调用：客户端发送问题，服务端流式返回答案
     * </pre>
     */
    public java.util.Iterator<com.deepknow.omniagent.grpc.ChatResponse> streamChat(
        com.deepknow.omniagent.grpc.ChatRequest request) {
      return io.grpc.stub.ClientCalls.blockingServerStreamingCall(
          getChannel(), getStreamChatMethod(), getCallOptions(), request);
    }

    /**
     * <pre>
     * 健康检查
     * </pre>
     */
    public com.deepknow.omniagent.grpc.HealthResponse healthCheck(com.deepknow.omniagent.grpc.HealthRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getHealthCheckMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service OmniAgentService.
   * <pre>
   * Omni-Agent gRPC 服务
   * 提供统一多模态 AI 能力
   * </pre>
   */
  public static final class OmniAgentServiceFutureStub
      extends io.grpc.stub.AbstractFutureStub<OmniAgentServiceFutureStub> {
    private OmniAgentServiceFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected OmniAgentServiceFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new OmniAgentServiceFutureStub(channel, callOptions);
    }

    /**
     * <pre>
     * 非流式多模态处理：支持 text + audio + image 组合输入
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<com.deepknow.omniagent.grpc.MultiModalResponse> process(
        com.deepknow.omniagent.grpc.MultiModalRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getProcessMethod(), getCallOptions()), request);
    }

    /**
     * <pre>
     * 健康检查
     * </pre>
     */
    public com.google.common.util.concurrent.ListenableFuture<com.deepknow.omniagent.grpc.HealthResponse> healthCheck(
        com.deepknow.omniagent.grpc.HealthRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getHealthCheckMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_PROCESS = 0;
  private static final int METHODID_STREAM_CHAT = 1;
  private static final int METHODID_HEALTH_CHECK = 2;
  private static final int METHODID_PROCESS_STREAM = 3;
  private static final int METHODID_STREAM_STT = 4;

  private static final class MethodHandlers<Req, Resp> implements
      io.grpc.stub.ServerCalls.UnaryMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ServerStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.ClientStreamingMethod<Req, Resp>,
      io.grpc.stub.ServerCalls.BidiStreamingMethod<Req, Resp> {
    private final AsyncService serviceImpl;
    private final int methodId;

    MethodHandlers(AsyncService serviceImpl, int methodId) {
      this.serviceImpl = serviceImpl;
      this.methodId = methodId;
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public void invoke(Req request, io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        case METHODID_PROCESS:
          serviceImpl.process((com.deepknow.omniagent.grpc.MultiModalRequest) request,
              (io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.MultiModalResponse>) responseObserver);
          break;
        case METHODID_STREAM_CHAT:
          serviceImpl.streamChat((com.deepknow.omniagent.grpc.ChatRequest) request,
              (io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.ChatResponse>) responseObserver);
          break;
        case METHODID_HEALTH_CHECK:
          serviceImpl.healthCheck((com.deepknow.omniagent.grpc.HealthRequest) request,
              (io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.HealthResponse>) responseObserver);
          break;
        default:
          throw new AssertionError();
      }
    }

    @java.lang.Override
    @java.lang.SuppressWarnings("unchecked")
    public io.grpc.stub.StreamObserver<Req> invoke(
        io.grpc.stub.StreamObserver<Resp> responseObserver) {
      switch (methodId) {
        case METHODID_PROCESS_STREAM:
          return (io.grpc.stub.StreamObserver<Req>) serviceImpl.processStream(
              (io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.MultiModalStreamResponse>) responseObserver);
        case METHODID_STREAM_STT:
          return (io.grpc.stub.StreamObserver<Req>) serviceImpl.streamSTT(
              (io.grpc.stub.StreamObserver<com.deepknow.omniagent.grpc.SttResponse>) responseObserver);
        default:
          throw new AssertionError();
      }
    }
  }

  public static final io.grpc.ServerServiceDefinition bindService(AsyncService service) {
    return io.grpc.ServerServiceDefinition.builder(getServiceDescriptor())
        .addMethod(
          getProcessMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.deepknow.omniagent.grpc.MultiModalRequest,
              com.deepknow.omniagent.grpc.MultiModalResponse>(
                service, METHODID_PROCESS)))
        .addMethod(
          getProcessStreamMethod(),
          io.grpc.stub.ServerCalls.asyncBidiStreamingCall(
            new MethodHandlers<
              com.deepknow.omniagent.grpc.MultiModalStreamRequest,
              com.deepknow.omniagent.grpc.MultiModalStreamResponse>(
                service, METHODID_PROCESS_STREAM)))
        .addMethod(
          getStreamSTTMethod(),
          io.grpc.stub.ServerCalls.asyncBidiStreamingCall(
            new MethodHandlers<
              com.deepknow.omniagent.grpc.SttRequest,
              com.deepknow.omniagent.grpc.SttResponse>(
                service, METHODID_STREAM_STT)))
        .addMethod(
          getStreamChatMethod(),
          io.grpc.stub.ServerCalls.asyncServerStreamingCall(
            new MethodHandlers<
              com.deepknow.omniagent.grpc.ChatRequest,
              com.deepknow.omniagent.grpc.ChatResponse>(
                service, METHODID_STREAM_CHAT)))
        .addMethod(
          getHealthCheckMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              com.deepknow.omniagent.grpc.HealthRequest,
              com.deepknow.omniagent.grpc.HealthResponse>(
                service, METHODID_HEALTH_CHECK)))
        .build();
  }

  private static abstract class OmniAgentServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    OmniAgentServiceBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return com.deepknow.omniagent.grpc.OmniAgentProto.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("OmniAgentService");
    }
  }

  private static final class OmniAgentServiceFileDescriptorSupplier
      extends OmniAgentServiceBaseDescriptorSupplier {
    OmniAgentServiceFileDescriptorSupplier() {}
  }

  private static final class OmniAgentServiceMethodDescriptorSupplier
      extends OmniAgentServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    OmniAgentServiceMethodDescriptorSupplier(java.lang.String methodName) {
      this.methodName = methodName;
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.MethodDescriptor getMethodDescriptor() {
      return getServiceDescriptor().findMethodByName(methodName);
    }
  }

  private static volatile io.grpc.ServiceDescriptor serviceDescriptor;

  public static io.grpc.ServiceDescriptor getServiceDescriptor() {
    io.grpc.ServiceDescriptor result = serviceDescriptor;
    if (result == null) {
      synchronized (OmniAgentServiceGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new OmniAgentServiceFileDescriptorSupplier())
              .addMethod(getProcessMethod())
              .addMethod(getProcessStreamMethod())
              .addMethod(getStreamSTTMethod())
              .addMethod(getStreamChatMethod())
              .addMethod(getHealthCheckMethod())
              .build();
        }
      }
    }
    return result;
  }
}
