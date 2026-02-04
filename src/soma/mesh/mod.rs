// mod.rs
/*!
MODULE: body::mesh

ROLE:
    P2P Nervous System.
    Handles QUIC/Cap'n Proto transport between nodes.
    Responsible for Gossip and Direct messaging.

OWNERSHIP:
    Body subsystem.

DO NOT:
    - Decrypt content (Pass abstract packets to Brain)
    - Leak IP addresses

PUBLIC API:
    - connect(peer_id) -> Connection
    - broadcast(msg) -> Result
    - listen() -> Stream

ENTRYPOINTS:
    body::mesh::service
*/
