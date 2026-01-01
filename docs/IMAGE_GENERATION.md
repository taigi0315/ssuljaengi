# Image Generation Implementation Guide

## Critical Configuration

### Model Selection

**MUST USE: `gemini-2.5-flash-image`**

This is the ONLY model that supports native image generation via the Google GenAI SDK on the free tier.

### Why This Specific Model?

1. **Free Tier Access**: `gemini-2.5-flash-image` is available on Google's free tier
2. **Native Image Generation**: Returns images as `inline_data` in response parts
3. **No Special Configuration**: Does NOT require `response_mime_type` or other config

### What DOESN'T Work (Lessons Learned)

❌ **`imagen-3.0-generate-001`**: Returns `404 Not Found` (requires paid tier or whitelist)
❌ **`image-generation-002`**: Returns `404 Not Found` (Imagen 2 is restricted)
❌ **`gemini-2.0-flash-exp`**: Does NOT support image generation (text-only model)
❌ **Setting `response_mime_type="image/png"`**: Returns `400 INVALID_ARGUMENT` (not supported for image generation)

## Implementation Architecture

### Current Design (google-genai SDK)

We use the **`google-genai`** Python SDK (NOT LangChain, NOT raw REST API):

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-2.5-flash-image",  # CRITICAL: Must be this exact model
    contents=[prompt],
    # NO config parameter needed for image generation
)

# Extract image from response
for part in response.parts:
    if part.inline_data is not None:
        image_bytes = part.inline_data.data
        # Save image_bytes to file
```

### Why NOT LangChain?

Initial design considered LangChain, but we switched to direct SDK usage because:

- **Simpler**: Direct SDK has fewer abstraction layers
- **More Control**: Direct access to response structure
- **Better Documentation**: Official Google docs use this pattern
- **Free Tier Compatible**: LangChain's image generation wrappers may not support free tier models

### Why NOT REST API?

- **Complexity**: Requires manual request construction and authentication
- **Maintenance**: SDK handles API version changes automatically
- **Type Safety**: SDK provides proper Python types and validation

## File Structure

### Image Generation Components

```
src/gossiptoon/visual/
├── base.py              # Abstract ImageClient interface
├── gemini_client.py     # GeminiImageClient implementation (MAIN)
├── director.py          # VisualDirector orchestrates image generation
└── character_bank.py    # Character consistency management
```

### Key Implementation: `GeminiImageClient`

**File**: `src/gossiptoon/visual/gemini_client.py`

**Critical Code Section** (lines 102-166):

```python
# Use Gemini 2.5 Flash Image (official image generation model)
# Docs: https://ai.google.dev/gemini-api/docs/image-generation
from google import genai

client = genai.Client(api_key=self.api_key)

response = client.models.generate_content(
    model="gemini-2.5-flash-image",  # DO NOT CHANGE THIS
    contents=[image_prompt],
)

# Image comes back as inline_data automatically
for part in response.parts:
    if part.inline_data is not None:
        image_data = part.inline_data.data
        break
```

## Debugging History (2026-01-01)

### Timeline of Issues

1. **10:34 AM**: Pipeline used `imagen-3.0-generate-001` → `404 Not Found`
   - **Fallback**: Generated plain color placeholder images
2. **11:00 AM**: Attempted fix with `image-generation-002` → Still `404 Not Found`
   - **Root Cause**: Both Imagen models require paid tier
3. **11:09 AM**: Removed fallback logic (strict failure policy)
   - **Result**: Pipeline now crashes on image failure (desired behavior)
4. **11:14 AM**: Attempted `gemini-2.0-flash-exp` with `response_mime_type="image/png"` → `400 INVALID_ARGUMENT`
   - **Root Cause**: Wrong model + invalid config
5. **11:20 AM**: **FINAL FIX** - Changed to `gemini-2.5-flash-image` without config
   - **Result**: ✅ Working image generation

### Key Learnings

1. **Model Names Matter**: Gemini has multiple models with different capabilities
2. **Free Tier Limitations**: Imagen models are NOT available on free tier
3. **API Evolution**: Google's image generation API changed from Imagen to Gemini-native
4. **Documentation is King**: Official Google docs had the correct answer all along

## Testing

### Manual Verification

To test image generation:

```bash
cd /Users/changikchoi/Documents/Github/ssuljaengi
python -c "
from google import genai
client = genai.Client(api_key='YOUR_API_KEY')
response = client.models.generate_content(
    model='gemini-2.5-flash-image',
    contents=['A red apple on a white table']
)
for part in response.parts:
    if part.inline_data:
        with open('test.png', 'wb') as f:
            f.write(part.inline_data.data)
        print('✅ Image saved to test.png')
        break
"
```

### Expected Behavior

- ✅ Image saved successfully
- ✅ No `404` or `400` errors
- ✅ `inline_data` present in response parts

## References

- **Official Docs**: https://ai.google.dev/gemini-api/docs/image-generation
- **Python SDK**: https://github.com/googleapis/python-genai
- **Model List**: https://ai.google.dev/gemini-api/docs/models/gemini

## Maintenance Notes

### If Image Generation Breaks Again

1. **Check Model Availability**: Verify `gemini-2.5-flash-image` is still available
2. **Check API Key**: Ensure API key has image generation permissions
3. **Check Quota**: Free tier has rate limits (check Google AI Studio)
4. **Check SDK Version**: Ensure `google-genai` is up to date

### Future Considerations

- **Paid Tier**: If upgrading to paid tier, consider Imagen 3 for higher quality
- **Batch Generation**: Implement batch processing for multiple images
- **Caching**: Consider caching generated images to reduce API calls
- **Alternative Providers**: If Google changes pricing, evaluate Stability AI, DALL-E, etc.

---

**Last Updated**: 2026-01-01  
**Author**: Debugging session with Claude (Sonnet 4.5)  
**Status**: ✅ Working Configuration
