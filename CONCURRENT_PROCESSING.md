# Concurrent VLM Processing

The PDF Visual Extraction library now supports concurrent processing for VLM (Visual Language Model) operations, providing significant speed improvements.

## Performance Benefits

### Before (Sequential Processing)
- 10 pages × 3 seconds each = **30 seconds**
- One page processed at a time
- Limited by API response time

### After (Concurrent Processing)
- 10 pages ÷ 5 workers × 3 seconds = **6 seconds**
- **5x faster processing!**
- Multiple pages processed simultaneously

## Usage

### Command Line Interface
```bash
python pdf_visual_extract.py \
  --pdf_path "document.pdf" \
  --output_dir "output/" \
  --max_workers 5 \
  --export_md
```

### Python API
```python
from pdf_visual_extract import run_pdf_visual_extraction

success = run_pdf_visual_extraction(
    pdf_path="document.pdf",
    output_dir="output/",
    max_pages=10,
    export_md=True,
    max_workers=5  # 5 concurrent workers
)
```

### Jupyter Notebook
```python
# See demo_usage.ipynb for complete example
success = run_pdf_visual_extraction(
    pdf_path="../data/document.pdf",
    output_dir="../output/",
    max_workers=5
)
```

## Configuration Options

### Worker Count Recommendations

| API Tier | Recommended Workers | Use Case |
|----------|-------------------|----------|
| Free Tier | 1-2 | Testing, small documents |
| Pay-as-you-go | 3-5 | Production, medium documents |
| Enterprise | 10+ | High-volume processing |

### Rate Limiting Considerations

OpenAI has rate limits that vary by tier:
- **Free tier**: 3 requests per minute
- **Pay-as-you-go**: 3,500 requests per minute
- **Enterprise**: Custom limits

Adjust `max_workers` based on your API tier to avoid rate limit errors.

## Technical Details

### Implementation
- Uses `ThreadPoolExecutor` for concurrent processing
- Each worker gets its own OpenAI client instance
- Results are collected and sorted by page number
- Error handling per worker with graceful degradation

### Memory Usage
- Each worker loads one image at a time
- Base64 encoding happens per request
- Memory usage scales linearly with worker count

### Error Handling
- Individual worker failures don't stop the pipeline
- Failed pages are logged with error details
- Successful pages are still processed and saved

## Example Performance Test

```python
# Test different worker configurations
import time

configs = [
    (1, "Sequential"),
    (3, "3 Workers"), 
    (5, "5 Workers"),
    (10, "10 Workers")
]

for workers, name in configs:
    start = time.time()
    success = run_pdf_visual_extraction(
        pdf_path="test.pdf",
        output_dir=f"output_{workers}workers/",
        max_workers=workers
    )
    duration = time.time() - start
    print(f"{name}: {duration:.2f}s")
```

## Best Practices

1. **Start Conservative**: Begin with 3-5 workers
2. **Monitor Rate Limits**: Watch for 429 errors
3. **Test Your Setup**: Run small tests first
4. **Consider API Costs**: More workers = more API calls
5. **Use Skip Logic**: Set `force=False` to avoid reprocessing

## Troubleshooting

### Common Issues

**Rate Limit Errors (429)**
- Reduce `max_workers`
- Add delays between requests
- Check your API tier limits

**Memory Issues**
- Reduce `max_workers`
- Process fewer pages at once
- Increase system memory

**Timeout Errors**
- Check network connectivity
- Verify API key is valid
- Try with fewer workers

### Debug Mode
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with single worker for debugging
success = run_pdf_visual_extraction(
    pdf_path="document.pdf",
    output_dir="output/",
    max_workers=1  # Debug with single worker
)
```

## Migration from Sequential

The concurrent processing is backward compatible:
- Default `max_workers=5` (was sequential before)
- All existing code works without changes
- Add `max_workers` parameter for speed improvements

```python
# Old code (still works)
success = run_pdf_visual_extraction(pdf_path, output_dir)

# New code (faster)
success = run_pdf_visual_extraction(pdf_path, output_dir, max_workers=5)
```
