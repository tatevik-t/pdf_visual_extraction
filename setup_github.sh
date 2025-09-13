#!/bin/bash

# Setup script for GitHub repository

echo "🚀 Setting up PDF Visual Extraction Library for GitHub..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
fi

# Add all files
echo "📁 Adding files to git..."
git add .

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: PDF Visual Extraction Library v1.0.0

- Complete PDF text extraction and visual element detection
- OpenAI GPT-4o-mini integration for table/figure detection
- Multiple export formats (JSON, Markdown, PDF)
- Command line interface and Python API
- Comprehensive documentation and examples
- CI/CD pipeline with GitHub Actions
- Full test suite and type checking"

# Create main branch
echo "🌿 Creating main branch..."
git branch -M main

echo "✅ Local repository setup complete!"
echo ""
echo "Next steps:"
echo "1. Create a new repository on GitHub: https://github.com/new"
echo "2. Add the remote origin:"
echo "   git remote add origin https://github.com/yourusername/pdf-visual-extraction.git"
echo "3. Push to GitHub:"
echo "   git push -u origin main"
echo ""
echo "📋 Repository structure:"
echo "├── pdf_visual_extraction/     # Main library package"
echo "├── tests/                     # Test suite"
echo "├── examples/                  # Usage examples"
echo "├── docs/                      # Documentation"
echo "├── .github/workflows/         # CI/CD pipeline"
echo "├── setup.py                   # Package setup"
echo "├── requirements.txt           # Dependencies"
echo "├── README.md                  # Main documentation"
echo "└── LICENSE                    # MIT License"
echo ""
echo "🎉 Ready to push to GitHub!"
