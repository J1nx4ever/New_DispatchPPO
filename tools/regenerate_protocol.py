"""Rebuild from the authoritative Maven proto, compare Java/Python descriptors, deploy.
Run with the project's Python environment; Java/Maven dependencies must be installed.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from google.protobuf import descriptor_pb2

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'proto-src/src/main/proto/dispatch.proto'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    shutil.copyfile(SOURCE, ROOT / 'proto/dispatch.proto')
    subprocess.run([sys.executable, '-m', 'grpc_tools.protoc', '-I'+str(SOURCE.parent),
                    '--python_out='+str(ROOT/'python/generated'),
                    '--grpc_python_out='+str(ROOT/'python/generated'),str(SOURCE)],check=True)
    stub = ROOT/'python/generated/dispatch_pb2_grpc.py'
    stub.write_text(stub.read_text().replace('import dispatch_pb2 as dispatch__pb2','from . import dispatch_pb2 as dispatch__pb2'))
    subprocess.run(['mvn','-o','-q','-f',str(ROOT/'proto-src/pom.xml'),'package'],check=True)
    jar=ROOT/'proto-src/target/DRL-Dispatching-1.2.0.jar'
    protobuf=Path.home()/'.m2/repository/com/google/protobuf/protobuf-java/3.25.3/protobuf-java-3.25.3.jar'
    with tempfile.TemporaryDirectory() as tmp:
        cp=f'{jar}:{protobuf}'
        subprocess.run(['javac','-cp',cp,'-d',tmp,str(ROOT/'tools/ProtocolDescriptor.java')],check=True)
        desc=Path(tmp)/'java.pb'
        subprocess.run(['java','-cp',f'{tmp}:{cp}','ProtocolDescriptor',str(desc)],check=True)
        sys.path.insert(0,str(ROOT))
        from python.generated import dispatch_pb2
        java=descriptor_pb2.FileDescriptorProto.FromString(desc.read_bytes())
        py=descriptor_pb2.FileDescriptorProto.FromString(dispatch_pb2.DESCRIPTOR.serialized_pb)
        # protoc versions differ in materialization of default json_name.
        def clear_json(msg):
            for f in msg.field: f.ClearField('json_name')
            for nested in msg.nested_type: clear_json(nested)
        for d in (java,py):
            for msg in d.message_type: clear_json(msg)
        if java != py:
            raise RuntimeError('Java and Python protocol descriptors disagree')
        descriptor_hash=hashlib.sha256(py.SerializeToString(deterministic=True)).hexdigest()
    shutil.copyfile(jar,ROOT/'dist'/jar.name)
    manifest=dict(authority='proto-src/src/main/proto/dispatch.proto',proto_sha256=sha(SOURCE),
                  jar_sha256=sha(jar),normalized_descriptor_sha256=descriptor_hash,
                  python_generated_sha256={p.name:sha(p) for p in (ROOT/'python/generated').glob('dispatch_pb2*.py')},
                  java_protobuf='3.25.3',java_grpc='1.64.0',java_python_descriptor_equal=True)
    (ROOT/'dist/protocol_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__': main()
