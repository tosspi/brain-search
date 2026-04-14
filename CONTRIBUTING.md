# Contributing to Brain

Thank you for your interest in contributing!

## Development Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/brain-search.git
cd brain-search

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install in development mode
pip install -e .

# Run tests
python -m pytest tests/
```

## Code Style

- Follow PEP 8
- Use type hints
- Add docstrings for public functions
- Keep functions under 50 lines when possible

## Submitting Changes

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Commit (`git commit -m 'Add amazing feature'`)
7. Push (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Reporting Issues

When reporting issues, please include:
- Python version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Error messages (if any)

## Areas for Contribution

- [ ] Additional embedding models
- [ ] Performance optimizations
- [ ] More test coverage
- [ ] Documentation improvements
- [ ] Language support

## Code of Conduct

Be respectful and constructive in all interactions.
