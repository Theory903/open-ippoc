# IPPOC Development Guidelines

## Code Organization

### Module Structure
- **Core**: Shared utilities, constants, and common types
- **Network**: Mesh networking, gossip protocols, communication
- **Memory**: Storage systems, cognitive memory, retrieval
- **Cognition**: Reasoning engines, planners, decision makers
- **Economy**: Resource allocation, budgeting, market systems
- **Evolution**: Learning systems, policy enforcement, adaptation
- **Security**: Identity management, authentication, access control

### Naming Conventions
- Modules: `snake_case`
- Structs/Enums: `PascalCase`
- Functions: `snake_case`
- Constants: `UPPER_SNAKE_CASE`

## Testing

```bash
# Run all tests
cargo test
python -m pytest tests/

# Run specific test suite
cargo test network
python -m pytest tests/unit/
```

## Documentation

All public APIs should include doc comments following Rust documentation standards.

## Version Control

- Feature branches: `feature/<description>`
- Bug fixes: `fix/<description>`
- Releases: Semantic versioning