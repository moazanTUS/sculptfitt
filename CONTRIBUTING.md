# Contributing to SculpFit

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

### 1. Fork & Clone
```bash
git clone https://github.com/your-username/sculptfitt.git
cd sculpt
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Setup
```bash
cp .env.example .env
# Edit .env with your development values
```

### 5. Run Locally
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## Making Changes

### Code Style
- Follow PEP 8 for Python code
- Use 4 spaces for indentation
- Keep lines under 100 characters
- Use descriptive variable names

### Creating a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### Commit Messages
```
feat: Add new feature
fix: Fix bug in component
docs: Update documentation
style: Format code
refactor: Reorganize code structure
```

### Testing Before Push
```bash
# Check for syntax errors
python -m py_compile backend/main.py

# Test rate limiting
# (See API.md for testing instructions)

# Test endpoints locally
curl http://localhost:8000/health
```

## Pull Request Process

1. **Update documentation**
   - Update README.md if needed
   - Update API.md for endpoint changes
   - Add docstrings to new functions

2. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

3. **Create Pull Request**
   - Title: Clear description of changes
   - Description: What changed and why
   - Reference related issues
   - Include screenshots if UI changes

4. **Code Review**
   - Address review comments
   - Push changes to same branch
   - PR auto-updates

5. **Merge**
   - Maintainer merges after approval
   - Railway auto-deploys to production

## Areas to Contribute

### Backend
- [ ] New analyzer for different exercises
- [ ] Improved plan matching algorithm
- [ ] New API endpoints
- [ ] Database optimizations
- [ ] Bug fixes

### Frontend
- [ ] UI/UX improvements
- [ ] Better progress visualizations
- [ ] Mobile optimization
- [ ] Accessibility improvements
- [ ] Bug fixes

### Documentation
- [ ] Improve existing docs
- [ ] Add tutorials
- [ ] Add troubleshooting guides
- [ ] Improve code comments

### Testing
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Test on different browsers
- [ ] Load testing

## Code Review Guidelines

When submitting a PR:
- Keep changes focused and minimal
- Add comments for complex logic
- Include type hints where possible
- Test edge cases
- Ensure backwards compatibility

When reviewing:
- Check for correctness
- Verify performance implications
- Look for security issues
- Suggest improvements kindly
- Approve once satisfied

## Known Issues & Limitations

See [GitHub Issues](https://github.com/moazanTUS/sculptfitt/issues) for:
- Reported bugs
- Feature requests
- Enhancement ideas

## Need Help?

- **Questions?** Open a Discussion on GitHub
- **Bug found?** Create an Issue with details
- **Feature idea?** Start a Discussion first

## Code of Conduct

- Be respectful to all contributors
- Welcome diverse perspectives
- Focus on the code, not the person
- Help newcomers feel welcome
- Report inappropriate behavior

## License

By contributing, you agree your changes will be licensed under the same license as the project.

---

Happy coding! 🚀

