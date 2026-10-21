package DRL.grpc;

import static io.grpc.MethodDescriptor.generateFullMethodName;

/**
 */
@javax.annotation.Generated(
    value = "by gRPC proto compiler (version 1.64.0)",
    comments = "Source: dispatch.proto")
@io.grpc.stub.annotations.GrpcGenerated
public final class DispatchServiceGrpc {

  private DispatchServiceGrpc() {}

  public static final java.lang.String SERVICE_NAME = "DRL.grpc.DispatchService";

  // Static method descriptors that strictly reflect the proto.
  private static volatile io.grpc.MethodDescriptor<DRL.grpc.DispatchRequest,
      DRL.grpc.DispatchResponse> getGetNextDestinationMethod;

  @io.grpc.stub.annotations.RpcMethod(
      fullMethodName = SERVICE_NAME + '/' + "GetNextDestination",
      requestType = DRL.grpc.DispatchRequest.class,
      responseType = DRL.grpc.DispatchResponse.class,
      methodType = io.grpc.MethodDescriptor.MethodType.UNARY)
  public static io.grpc.MethodDescriptor<DRL.grpc.DispatchRequest,
      DRL.grpc.DispatchResponse> getGetNextDestinationMethod() {
    io.grpc.MethodDescriptor<DRL.grpc.DispatchRequest, DRL.grpc.DispatchResponse> getGetNextDestinationMethod;
    if ((getGetNextDestinationMethod = DispatchServiceGrpc.getGetNextDestinationMethod) == null) {
      synchronized (DispatchServiceGrpc.class) {
        if ((getGetNextDestinationMethod = DispatchServiceGrpc.getGetNextDestinationMethod) == null) {
          DispatchServiceGrpc.getGetNextDestinationMethod = getGetNextDestinationMethod =
              io.grpc.MethodDescriptor.<DRL.grpc.DispatchRequest, DRL.grpc.DispatchResponse>newBuilder()
              .setType(io.grpc.MethodDescriptor.MethodType.UNARY)
              .setFullMethodName(generateFullMethodName(SERVICE_NAME, "GetNextDestination"))
              .setSampledToLocalTracing(true)
              .setRequestMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  DRL.grpc.DispatchRequest.getDefaultInstance()))
              .setResponseMarshaller(io.grpc.protobuf.ProtoUtils.marshaller(
                  DRL.grpc.DispatchResponse.getDefaultInstance()))
              .setSchemaDescriptor(new DispatchServiceMethodDescriptorSupplier("GetNextDestination"))
              .build();
        }
      }
    }
    return getGetNextDestinationMethod;
  }

  /**
   * Creates a new async stub that supports all call types for the service
   */
  public static DispatchServiceStub newStub(io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<DispatchServiceStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<DispatchServiceStub>() {
        @java.lang.Override
        public DispatchServiceStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new DispatchServiceStub(channel, callOptions);
        }
      };
    return DispatchServiceStub.newStub(factory, channel);
  }

  /**
   * Creates a new blocking-style stub that supports unary and streaming output calls on the service
   */
  public static DispatchServiceBlockingStub newBlockingStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<DispatchServiceBlockingStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<DispatchServiceBlockingStub>() {
        @java.lang.Override
        public DispatchServiceBlockingStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new DispatchServiceBlockingStub(channel, callOptions);
        }
      };
    return DispatchServiceBlockingStub.newStub(factory, channel);
  }

  /**
   * Creates a new ListenableFuture-style stub that supports unary calls on the service
   */
  public static DispatchServiceFutureStub newFutureStub(
      io.grpc.Channel channel) {
    io.grpc.stub.AbstractStub.StubFactory<DispatchServiceFutureStub> factory =
      new io.grpc.stub.AbstractStub.StubFactory<DispatchServiceFutureStub>() {
        @java.lang.Override
        public DispatchServiceFutureStub newStub(io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
          return new DispatchServiceFutureStub(channel, callOptions);
        }
      };
    return DispatchServiceFutureStub.newStub(factory, channel);
  }

  /**
   */
  public interface AsyncService {

    /**
     */
    default void getNextDestination(DRL.grpc.DispatchRequest request,
        io.grpc.stub.StreamObserver<DRL.grpc.DispatchResponse> responseObserver) {
      io.grpc.stub.ServerCalls.asyncUnimplementedUnaryCall(getGetNextDestinationMethod(), responseObserver);
    }
  }

  /**
   * Base class for the server implementation of the service DispatchService.
   */
  public static abstract class DispatchServiceImplBase
      implements io.grpc.BindableService, AsyncService {

    @java.lang.Override public final io.grpc.ServerServiceDefinition bindService() {
      return DispatchServiceGrpc.bindService(this);
    }
  }

  /**
   * A stub to allow clients to do asynchronous rpc calls to service DispatchService.
   */
  public static final class DispatchServiceStub
      extends io.grpc.stub.AbstractAsyncStub<DispatchServiceStub> {
    private DispatchServiceStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected DispatchServiceStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new DispatchServiceStub(channel, callOptions);
    }

    /**
     */
    public void getNextDestination(DRL.grpc.DispatchRequest request,
        io.grpc.stub.StreamObserver<DRL.grpc.DispatchResponse> responseObserver) {
      io.grpc.stub.ClientCalls.asyncUnaryCall(
          getChannel().newCall(getGetNextDestinationMethod(), getCallOptions()), request, responseObserver);
    }
  }

  /**
   * A stub to allow clients to do synchronous rpc calls to service DispatchService.
   */
  public static final class DispatchServiceBlockingStub
      extends io.grpc.stub.AbstractBlockingStub<DispatchServiceBlockingStub> {
    private DispatchServiceBlockingStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected DispatchServiceBlockingStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new DispatchServiceBlockingStub(channel, callOptions);
    }

    /**
     */
    public DRL.grpc.DispatchResponse getNextDestination(DRL.grpc.DispatchRequest request) {
      return io.grpc.stub.ClientCalls.blockingUnaryCall(
          getChannel(), getGetNextDestinationMethod(), getCallOptions(), request);
    }
  }

  /**
   * A stub to allow clients to do ListenableFuture-style rpc calls to service DispatchService.
   */
  public static final class DispatchServiceFutureStub
      extends io.grpc.stub.AbstractFutureStub<DispatchServiceFutureStub> {
    private DispatchServiceFutureStub(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      super(channel, callOptions);
    }

    @java.lang.Override
    protected DispatchServiceFutureStub build(
        io.grpc.Channel channel, io.grpc.CallOptions callOptions) {
      return new DispatchServiceFutureStub(channel, callOptions);
    }

    /**
     */
    public com.google.common.util.concurrent.ListenableFuture<DRL.grpc.DispatchResponse> getNextDestination(
        DRL.grpc.DispatchRequest request) {
      return io.grpc.stub.ClientCalls.futureUnaryCall(
          getChannel().newCall(getGetNextDestinationMethod(), getCallOptions()), request);
    }
  }

  private static final int METHODID_GET_NEXT_DESTINATION = 0;

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
        case METHODID_GET_NEXT_DESTINATION:
          serviceImpl.getNextDestination((DRL.grpc.DispatchRequest) request,
              (io.grpc.stub.StreamObserver<DRL.grpc.DispatchResponse>) responseObserver);
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
        default:
          throw new AssertionError();
      }
    }
  }

  public static final io.grpc.ServerServiceDefinition bindService(AsyncService service) {
    return io.grpc.ServerServiceDefinition.builder(getServiceDescriptor())
        .addMethod(
          getGetNextDestinationMethod(),
          io.grpc.stub.ServerCalls.asyncUnaryCall(
            new MethodHandlers<
              DRL.grpc.DispatchRequest,
              DRL.grpc.DispatchResponse>(
                service, METHODID_GET_NEXT_DESTINATION)))
        .build();
  }

  private static abstract class DispatchServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoFileDescriptorSupplier, io.grpc.protobuf.ProtoServiceDescriptorSupplier {
    DispatchServiceBaseDescriptorSupplier() {}

    @java.lang.Override
    public com.google.protobuf.Descriptors.FileDescriptor getFileDescriptor() {
      return DRL.grpc.DispatchProto.getDescriptor();
    }

    @java.lang.Override
    public com.google.protobuf.Descriptors.ServiceDescriptor getServiceDescriptor() {
      return getFileDescriptor().findServiceByName("DispatchService");
    }
  }

  private static final class DispatchServiceFileDescriptorSupplier
      extends DispatchServiceBaseDescriptorSupplier {
    DispatchServiceFileDescriptorSupplier() {}
  }

  private static final class DispatchServiceMethodDescriptorSupplier
      extends DispatchServiceBaseDescriptorSupplier
      implements io.grpc.protobuf.ProtoMethodDescriptorSupplier {
    private final java.lang.String methodName;

    DispatchServiceMethodDescriptorSupplier(java.lang.String methodName) {
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
      synchronized (DispatchServiceGrpc.class) {
        result = serviceDescriptor;
        if (result == null) {
          serviceDescriptor = result = io.grpc.ServiceDescriptor.newBuilder(SERVICE_NAME)
              .setSchemaDescriptor(new DispatchServiceFileDescriptorSupplier())
              .addMethod(getGetNextDestinationMethod())
              .build();
        }
      }
    }
    return result;
  }
}
