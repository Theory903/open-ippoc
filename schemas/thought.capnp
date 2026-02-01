@0x934efea7f017fff0;

interface NervousSystem {
  # The core protocol for the P2P mesh
  
  struct Thought {
    taskId @0 :Data;
    embedding @1 :Data; # f32 vector
    confidence @2 :Float32;
    type @3 :Type;
    content @4 :Text;
    
    enum Type {
      plan @0;
      result @1;
      error @2;
      query @3;
    }
  }

  struct MemoryRecord {
    id @0 :Data; # UUID bytes
    embedding @1 :Data;
    content @2 :Text;
    confidence @3 :Float32;
    decayRate @4 :Float32;
    source @5 :Text;
  }
}
