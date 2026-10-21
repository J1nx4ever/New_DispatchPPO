import java.nio.file.Files;
import java.nio.file.Path;
public class ProtocolDescriptor {
    public static void main(String[] args) throws Exception {
        Files.write(Path.of(args[0]), DRL.grpc.DispatchProto.getDescriptor().toProto().toByteArray());
    }
}
