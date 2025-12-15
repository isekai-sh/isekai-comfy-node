# Isekai ComfyUI Custom Node

[![Latest Release](https://img.shields.io/github/v/release/isekai-sh/isekai-comfy-node)](https://github.com/isekai-sh/isekai-comfy-node/releases/latest)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/isekai-sh/isekai-comfy-node)](LICENSE)

Upload and compress AI-generated images and enhance your ComfyUI workflows with powerful string utilities and AI integration.

## Quick Download

**[📥 Download Latest Release](https://github.com/isekai-sh/isekai-comfy-node/releases/latest)**

Extract the ZIP file to `ComfyUI/custom_nodes/` and restart ComfyUI

## Features

### Image Processing

- **Isekai Upload**: Direct upload with built-in compression (JPEG/PNG, quality 90 default)
- **Isekai Compress and Save**: Compress and save images to disk (JPEG/PNG/WEBP)
- Reduce upload sizes by 80-90% with JPEG compression
- Support for titles, tags, and quality settings
- Comprehensive error handling and rate limiting protection

### String Utilities

- **Dynamic String**: Random line selector with reproducible seeds
- **Concatenate String**: Join up to 10 text inputs with custom delimiters
- **Tag Selector**: Dictionary-based tag lookup system
- **Round Robin**: Batch-completion cycler for equal distribution (e.g., 32 images per character)
- **Load Text**: Load text from files using dropdown selector or custom paths

### AI Integration

- **Ollama Summarizer**: Generate concise titles from prompts using local LLMs

## Requirements

- ComfyUI installed and running
- Python 3.8 or higher
- For upload functionality: Isekai account with API access
- For Ollama Summarizer: Local Ollama instance (optional)

## Installation

### Option 1: Download Release (Recommended)

1. **[Download the latest release](https://github.com/isekai-sh/isekai-comfy-node/releases/latest)**
2. Extract the ZIP file to `ComfyUI/custom_nodes/` (the folder should be named `isekai-comfy-node`)
3. Open a terminal in the extracted folder
4. Run: `pip install -r requirements.txt`
5. Restart ComfyUI

### Option 2: Git Clone

1. Open a terminal in `ComfyUI/custom_nodes/`
2. Run: `git clone https://github.com/isekai-sh/isekai-comfy-node.git`
3. Run: `cd isekai-comfy-node && pip install -r requirements.txt`
4. Restart ComfyUI

## Getting Your API Key

1. Log in to your Isekai account at [https://app.isekai.sh](https://app.isekai.sh)
2. Navigate to **Profile > API Keys**
3. Click **"Create New API Key"** (requires Pro account)
4. Give it a name (e.g., "ComfyUI")
5. Copy the API key (starts with `isk_...`)

**Important:** Your API key is only shown once. Save it somewhere secure.

## Setting Up API Key (Recommended Method)

For security, it's recommended to use environment variables instead of entering your API key directly in the node.

### Using Environment Variable (Secure)

Set the `ISEKAI_API_KEY` environment variable before starting ComfyUI:

**macOS/Linux:**

```bash
export ISEKAI_API_KEY=isk_your_api_key_here
```

**Windows (PowerShell):**

```powershell
$env:ISEKAI_API_KEY="isk_your_api_key_here"
```

**Windows (Command Prompt):**

```cmd
set ISEKAI_API_KEY=isk_your_api_key_here
```

Then restart ComfyUI. The upload node will automatically use the environment variable.

### Using Node Input (Fallback)

If you don't set the environment variable, you can enter your API key directly in the node's `api_key` field. However, this method:

- Exposes your API key in the node interface
- Saves your API key in workflow JSON files
- **Should not be used for workflows you plan to share publicly**

The environment variable method is more secure and prevents accidental exposure.

## Node Documentation

### 1. Isekai Upload

Upload generated images directly to the Isekai platform.

**Location:** Isekai > Isekai Upload

**Inputs:**

- `image` (IMAGE, required): Image tensor from any image-producing node
- `title` (STRING, required): Title for your artwork (max 200 characters, auto-truncated)
- `api_key` (STRING, optional): Your Isekai API key (format: `isk_[64 hex chars]`)
  - Leave empty to use `ISEKAI_API_KEY` environment variable (recommended)
  - Only use this field if you haven't set the environment variable
- `tags` (STRING, optional): Comma-separated tags (e.g., "fantasy, portrait, digital art")
- `format` (DROPDOWN, optional): Image format - JPEG or PNG (default: JPEG)
- `quality` (INT slider, optional): Compression quality 1-100 (default: 90)
  - Lower values = smaller file size, lower quality
  - Higher values = larger file size, better quality
  - JPEG quality 90 reduces file size by ~80-90% with excellent quality
  - PNG quality affects compress_level (higher quality = less compression)

**Outputs:**

- `IMAGE`: Pass-through of input image (enables preview)

**Example Workflow:**

```
VAE Decode → Isekai Upload → Preview Image
             ↓ api_key: isk_abc123...
             ↓ title: "Epic Fantasy Warrior"
             ↓ tags: "fantasy, warrior, armor"
```

**Compression Benefits:**

- **Reduce bandwidth**: JPEG quality 90 can reduce upload size by ~80-90% with excellent quality
- **Save storage**: Smaller files mean more uploads within storage quotas
- **Faster uploads**: Smaller files upload significantly faster
- **Format flexibility**: Choose PNG for lossless or JPEG for lossy compression

**Recommended Settings:**

- **High quality (default)**: JPEG, quality 90 (80-90% size reduction, excellent quality)
- **Balanced**: JPEG, quality 75-85 (85-92% size reduction, very good quality)
- **Maximum compression**: JPEG, quality 30-60 (93-95% size reduction, acceptable quality)
- **Lossless**: PNG, quality 100 (no quality loss, ~20-30% compression only)

**After Upload:**

- Images appear in Isekai dashboard with status "review"
- Approve or reject in the web interface
- Approved images move to Drafts for scheduling

---

### 2. Isekai Compress and Save

Compress and save images to disk with full control over format, quality, and filenames.

**Location:** Isekai > Isekai Compress and Save

**Inputs:**

- `images` (IMAGE, required): Image tensor from any image-producing node
- `filename` (STRING, required): Base filename (default: "isekai")
- `format` (DROPDOWN, required): Output format - JPEG, PNG, or WEBP (default: JPEG)
- `quality` (INT slider, required): Compression quality 1-100 (default: 90)
  - Lower = smaller files, lower quality
  - Higher = larger files, better quality

**Outputs:**

- None (terminal node - saves to disk)
- Images saved to `ComfyUI/output/` folder

**Format Options:**

- **PNG**: Lossless compression, supports transparency
- **JPEG**: Lossy compression, smaller files, no transparency
- **WEBP**: Modern format, excellent compression, best of both worlds

**Filename Pattern:**

```
{filename}_{counter}.{extension}

Examples:
- filename="artwork" → artwork_00001.jpg
- filename="character" → character_00001.jpg
- filename="render" → render_00001.webp
```

**Use Cases:**

- Save compressed images directly without intermediate nodes
- Batch save with automatic numbering
- Reduce disk space usage with quality control
- Quick export with custom filenames

**Example Workflow:**

```
VAE Decode → Isekai Compress and Save
             ↓ filename: "artwork"
             ↓ format: JPEG
             ↓ quality: 90
             → Saves to: output/artwork_00001.jpg
```

**High Quality PNG:**

```
VAE Decode → Isekai Compress and Save
             ↓ filename: "final_render"
             ↓ format: PNG
             ↓ quality: 95
             → Saves to: output/final_render_00001.png
```

**Console Output:**

```
[Isekai] Compressing and saving 1 image(s)...
[Isekai] Format: JPEG, Quality: 90
[Isekai] Save settings: {'quality': 90, 'optimize': True}
[Isekai] Saved: artwork_00001.jpg (156.34 KB)
```

**Tips:**

- ✅ Counter auto-increments to avoid overwriting files
- ✅ JPEG quality 90 (default) is recommended for excellent quality with good compression
- ✅ PNG with high quality (90-100) for archival or when transparency is needed
- ✅ WEBP offers best compression but may have compatibility issues

---

### 3. Isekai Dynamic String

Randomly select one line from multiline text with reproducible results.

**Location:** Isekai > Isekai Dynamic String

**Inputs:**

- `text_list` (STRING, required, multiline): Lines of text (one option per line)
- `seed` (INT, required): Random seed for deterministic selection (0 to 2^64-1)

**Outputs:**

- `selected_string` (STRING): One randomly selected line

**Use Cases:**

- Random prompt selection for batch generation
- Varying art styles across multiple renders
- A/B testing different prompts with reproducible results

**Example:**

```
Input text_list:
portrait of a warrior
landscape with mountains
abstract digital art

Seed: 42
Output: "portrait of a warrior" (deterministic - same seed always returns same result)
```

**Workflow Integration:**

```
Isekai Dynamic String → Text Concatenate → CLIP Text Encode
 ↓ seed: 42
```

---

### 4. Isekai Concatenate String

Join multiple string inputs with a configurable delimiter.

**Location:** Isekai > Isekai Concatenate String

**Inputs:**

- `delimiter` (STRING, required): Character(s) to place between joined texts (default: " ")
- `text_a` through `text_j` (STRING, optional): Up to 10 text inputs (connect via node links)

**Outputs:**

- `concatenated_string` (STRING): Joined text (empty inputs are skipped)

**Use Cases:**

- Building complex prompts from multiple sources
- Combining base prompt with dynamic additions
- Creating structured text with custom formatting

**Example:**

```
text_a = "portrait of"
text_b = "a warrior"
text_c = "in golden armor"
delimiter = " "
Output: "portrait of a warrior in golden armor"
```

**With Custom Delimiter:**

```
text_a = "fantasy"
text_b = "warrior"
text_c = "armor"
delimiter = ", "
Output: "fantasy, warrior, armor"
```

**Workflow Integration:**

```
Dynamic String → text_a ┐
Tag Selector → text_b ─┼→ Concatenate String → CLIP Text Encode
Manual Text → text_c ┘   (delimiter: ", ")
```

---

### 5. Isekai Tag Selector

Dictionary-based tag lookup using trigger words with TOML/INI format.

**Location:** Isekai > Isekai Tag Selector

**Inputs:**

- `trigger_word` (STRING, required): Keyword to search for (connect via node link)
- `presets` (STRING, required, multiline): TOML/INI style sections with tags
- `default_value` (STRING, optional): Fallback value if trigger not found

**Outputs:**

- `selected_tags` (STRING): Matched tags or default value

**Format (TOML/INI Style):**

```
[TriggerWord]
tags, separated, by, commas

[AnotherTrigger]
more, tags, here
```

**Matching Rules:**

- Case-insensitive (Batman = batman = BATMAN)
- Whitespace-tolerant
- Empty lines are ignored
- Supports multi-line tags per section
- **Backward Compatible:** Still supports legacy `Key: value` format

**Use Cases:**

- Quick character tag sets
- Style presets
- Consistent tag application
- Load presets from files using Load Text node

**Example Presets:**

```
[Superman]
hero, flying, dc, blue suit, red cape, superhuman strength

[Batman]
dark, gotham, rich, bat signal, detective, vigilante

[Wonder Woman]
amazon, warrior, princess, tiara, lasso of truth

[Generic Hero]
superhero, powers, costume, save the day
```

**Usage:**

```
trigger_word = "batman"
Output: "dark, gotham, rich, bat signal, detective, vigilante"

trigger_word = "robin"  (not in presets)
default_value = "sidekick, hero"
Output: "sidekick, hero"
```

**Workflow Integration:**

```
Dynamic String ────→ trigger_word ┐
(random character)                 ├→ Tag Selector → Concatenate String
                    presets ←─────┘   (character tags)
```

**Advanced: Load from File:**

```
Load Text ──→ text_content ──→ presets ┐
(tag_presets.txt)                      ├→ Tag Selector
                         trigger_word ─┘
```

Where `tag_presets.txt` contains:

```
[Superman]
hero, flying, dc, blue suit, red cape

[Batman]
dark, gotham, rich, bat signal
```

---

### 6. Isekai Ollama Summarizer

Generate short, catchy titles from long prompts using local Ollama LLMs.

**Location:** Isekai > Isekai Ollama Summarizer

**Requirements:** Ollama running locally ([ollama.com](https://ollama.com))

**Inputs:**

- `text_input` (STRING, required): Long prompt text to summarize (connect via node link)
- `ollama_url` (STRING, required): Ollama server URL (default: "http://localhost:11434")
- `model` (DROPDOWN, required): LLM model to use (dynamically populated from Ollama)

**Outputs:**

- `title_summary` (STRING): Generated short title (or error message)

**Special Outputs:**

- `"Untitled"`: Empty input
- `"Connection Failed"`: Cannot reach Ollama
- `"Error: 404"`: Model not found

**Supported Models:**
Common models include: llama3, mistral, llama2, gemma, etc.

**Example:**

```
Input text_input:
"A highly detailed digital painting of a fierce warrior woman wearing ornate golden armor, standing heroically on a mountain peak at sunset with dramatic clouds in the background, fantasy art style"

model: llama3
Output: "Warrior at Golden Sunset"
```

**Workflow Integration:**

```
CLIP Text Encode ──→ text_input ┐
(full prompt)                    ├→ Ollama Summarizer → Isekai Upload
                     model: llama3                      (auto-generated title)
```

**Setup Ollama:**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3

# Verify it's running
curl http://localhost:11434/api/tags
```

### 7. Isekai Round Robin

Cycle through items in batch-completion mode using a round-robin pattern, ensuring equal distribution of images per item.

**Location:** Isekai > Isekai Round Robin

**Inputs:**

- `text_list` (STRING, required, multiline): Items to cycle through (one per line)
- `images_per_item` (INT, required): Number of images to generate per item (1-1000, default: 32)
- `batch_id` (STRING, required): Unique identifier for this batch job (default: "default")

**Outputs:**

- `selected_item` (STRING): Current item from the list
- `progress_info` (STRING): Progress indicator with both local and global progress (e.g., "Alice: 15/32 | Total: 15/96")
- `batch_count_needed` (INT): Total number of executions needed to complete all items (e.g., 96 for 3 items × 32 images)

**Behavior:**

- **Batch Completion**: Generates ALL images for Item A before moving to Item B
- **State Persistence**: State is bound to `batch_id` - different batch IDs maintain separate counters
- **Auto-Reset**: After all items complete, automatically cycles back to the first item
- **Auto-Cleanup**: State clears automatically when ComfyUI restarts (stored in temp directory)
- **Smart Progress**: Shows both item progress and overall completion
- **Multi-Batch Support**: Run multiple independent batches by using different batch IDs

**Use Cases:**

- **Characters**: `Alice\nBob\nCharlie` - generate 32 images per character
- **Props**: `sword\nshield\nbow` - generate equal images per prop
- **Environments**: `forest\ndesert\nmountain` - equal distribution per scene
- **Art Styles**: `oil painting\nwatercolor\ndigital` - cycle through styles

**How to Use:**

1. **Set a unique `batch_id`** (e.g., "character_batch_1", "props_batch_2")
2. **Set up your items** (one per line in `text_list`)
3. **Set `images_per_item`** (e.g., 32)
4. **Check the console output** on first run - you'll see:
   ```
   💡 TIP: Set batch count to 96 to complete all items
   3 items × 32 images = 96 total executions
   Batch ID: character_batch_1
   ```
5. **Set batch count to the suggested number** (or use `batch_count_needed` output)
6. **Queue once** and let it complete automatically!

**Example:**

```
Input:
  text_list: Alice\nBob\nCharlie
  images_per_item: 32
  batch_id: "character_batch_1"

Output on first run:
  Console: "💡 TIP: Set batch count to 96 to complete all items"
  Console: "3 items × 32 images = 96 total executions"
  Console: "Batch ID: character_batch_1"

Execution 1: "Alice", "Alice: 1/32 | Total: 1/96", 96
Execution 16: "Alice", "Alice: 16/32 | Total: 16/96", 96
Execution 32: "Alice", "Alice: 32/32 | Total: 32/96", 96
Execution 33: "Bob", "Bob: 1/32 | Total: 33/96", 96
Execution 96: "Charlie", "Charlie: 32/32 | Total: 96/96", 96
Execution 97: "Alice", "Alice: 1/32 | Total: 1/96", 96 (cycles back)
```

**Workflow Integration:**

```
Isekai Round Robin ──→ Isekai Tag Selector ──→ Isekai Concatenate String ──→ CLIP Text Encode
(batch completion)      (lookup item tags)      (build full prompt)
    │
    └─→ batch_count_needed ──→ Display/Note (shows "96")
```

**Multiple Independent Batches:**

```
Workflow 1:
  batch_id: "characters_batch"
  text_list: Alice\nBob\nCharlie
  → Counter at: Alice 15/32

Workflow 2:
  batch_id: "props_batch"
  text_list: sword\nshield\nbow
  → Counter at: shield 8/32

Both run independently with separate states!
```

**vs. Isekai Dynamic String:**

- **Dynamic String**: Random selection with seed (non-uniform distribution)
- **Round Robin**: Sequential batch completion (guaranteed uniform distribution)

**Tips:**

- ✅ **Use unique batch IDs**: Each batch job should have its own identifier (e.g., "batch_001", "characters_v2")
- ✅ **Use `batch_count_needed` output**: Connect to a display node to see exactly how many times to queue
- ✅ **Watch the console**: On initialization, you'll see helpful tips about batch count and batch ID
- ✅ **Monitor global progress**: The progress_info shows "Total: X/Y" so you always know where you are
- ✅ **Multiple batches**: Different batch_ids allow running multiple independent jobs simultaneously
- State is stored in `ComfyUI/temp/isekai/round_robin/{batch_id}.log`
- State automatically clears when ComfyUI restarts
- If you change `images_per_item` mid-batch, the counter resets automatically
- To start over: Restart ComfyUI or use a new batch_id

---

### 8. Isekai Load Text

Load text from a file and output it as a string using a dropdown selector or custom path.

**Location:** Isekai > Isekai Load Text

**Inputs (both optional, use one):**

- `text_file` (COMBO dropdown, optional): Select a file from `ComfyUI/models/text_files/` directory
- `custom_path` (STRING, optional): Enter absolute path for files outside the text_files directory

**Outputs:**

- `text_content` (STRING): Contents of the file as a string

**How to Use:**

**Method 1: Dropdown Selection (Recommended)**

1. Place your text files in `ComfyUI/models/text_files/` directory
2. Restart ComfyUI (or refresh node)
3. Select file from the dropdown menu
4. No path typing needed!

**Method 2: Custom Path**

1. Leave dropdown empty
2. Enter absolute path in `custom_path` field:
   - **macOS/Linux**: `/Users/username/prompts/characters.txt`
   - **Windows**: `C:\Users\username\prompts\characters.txt` or `D:\prompts\characters.txt`

**Priority:** If both inputs provided, `custom_path` takes precedence.

**Use Cases:**

- Load prompts from external files
- Load character lists for use with Round Robin or Dynamic String
- Load tag presets for Tag Selector
- Manage large text data externally instead of pasting into nodes
- Share prompt lists between multiple workflows

**Example Workflow:**

```
Isekai Load Text → Isekai Round Robin → Isekai Tag Selector → Concatenate
  (load list)        (cycle items)         (lookup tags)
```

**Error Handling:**

- Returns empty string if file doesn't exist
- Returns empty string if file can't be read
- Supports UTF-8 encoding with fallback to system default
- Prints helpful error messages to console
- Shows "(no files found - use custom path)" if text_files directory is empty

**Example (Dropdown Method):**

```
Setup:
  1. Create file: ComfyUI/models/text_files/characters.txt
  2. Add content: Alice\nBob\nCharlie
  3. Restart ComfyUI

Input:
  text_file: "characters.txt" (from dropdown)

Output:
  text_content: "Alice\nBob\nCharlie"

Console: "[Isekai] Load Text: Successfully loaded 20 characters from characters.txt"
```

**Example (Custom Path Method):**

```
Input:
  custom_path: "/Users/username/Documents/prompts/special_characters.txt"

Output:
  text_content: (file contents)

Console: "[Isekai] Load Text: Using custom path: /Users/username/Documents/prompts/special_characters.txt"
```

**Tips:**

- ✅ **Dropdown method**: Most convenient, no path typing, works cross-platform
- ✅ **Custom path**: Use for files outside text_files directory
- ✅ Works with any text file format (.txt, .md, .csv, etc.)
- ✅ Supports UTF-8 encoding with automatic fallback
- On first use, `ComfyUI/models/text_files/` directory is created automatically
- Place commonly used files in text_files directory for easy access
- Use custom path for one-off or external files

---

## Common Workflow Examples

### Example 1: Random Prompt with Upload

```
Isekai Dynamic String ──→ CLIP Text Encode ──→ Sampler ──→ VAE Decode ──→ Isekai Upload
 (random prompts)                                                         (auto-upload)
```

### Example 2: Character Tags with Title Generation

```
Dynamic String ──→ Tag Selector ──→ Concatenate ──→ CLIP Text Encode ──→ Sampler
(character name)   (character tags)   (full prompt)

                                                           ↓
                                                      VAE Decode
                                                           ↓
Ollama Summarizer ←───────────────────────────────── (pass prompt text)
(generate title)                                           ↓
       ↓                                              Isekai Upload
   title ──────────────────────────────────────────→ (upload with AI title)
```

### Example 3: Multi-Source Prompt Building

```
Dynamic String (style) ──→ text_a ┐
Tag Selector (tags) ─────→ text_b ├→ Concatenate ──→ CLIP Text Encode
Manual Text (details) ───→ text_c ┘   (delimiter: ", ")
```

## Configuration

### API URL (Optional)

By default, the upload node connects to `https://api.isekai.sh` (production).

For local development or testing:

```bash
# Linux/macOS
export ISEKAI_API_URL=http://localhost:4000

# Windows (PowerShell)
$env:ISEKAI_API_URL="http://localhost:4000"

# Windows (Command Prompt)
set ISEKAI_API_URL=http://localhost:4000
```

Then restart ComfyUI.

## Error Messages

| Error                    | Node   | Meaning                               | Solution                                                                       |
| ------------------------ | ------ | ------------------------------------- | ------------------------------------------------------------------------------ |
| "No API key provided"    | Upload | API key not found in env var or input | Set `ISEKAI_API_KEY` environment variable or enter key in node's api_key field |
| "Invalid API key format" | Upload | API key doesn't match expected format | Check that your API key starts with `isk_` and has 64 hex characters after it  |
| "Authentication failed"  | Upload | API key is invalid or revoked         | Generate a new API key in Isekai dashboard                                     |
| "Storage limit exceeded" | Upload | You've reached your storage quota     | Upgrade your subscription or delete old deviations                             |
| "Rate limit exceeded"    | Upload | Too many uploads in short time        | Wait 15 minutes before uploading again (limit: 100 uploads per 15 minutes)     |
| "Failed to connect"      | Upload | Network or API connection issue       | Check your internet connection and API URL configuration                       |
| "Upload timed out"       | Upload | Request took longer than 60 seconds   | Check your network connection and try again                                    |
| "Connection Failed"      | Ollama | Cannot reach Ollama server            | Start Ollama (`ollama serve`) and verify URL is correct                        |
| "Untitled"               | Ollama | Empty input provided                  | Connect a non-empty text input to the node                                     |

## Security Notes

**Recommended: Use Environment Variables**

The safest way to use your API key is through the `ISEKAI_API_KEY` environment variable:

✅ **Advantages:**

- API key is not visible in the node interface
- API key is not saved in workflow JSON files
- Workflows can be shared publicly without exposing credentials
- Easier to manage and rotate keys

❌ **Node Input Method (Not Recommended for Sharing):**

- API key is visible in the node interface
- API keys are saved in ComfyUI workflow JSON files
- **Do not share workflow files publicly** if they contain your API key
- Only use this method for private/local workflows

**Best Practices:**

- **Always use environment variables** when sharing workflows publicly
- Revoke and regenerate API keys if they're accidentally exposed
- Use descriptive names for your API keys (e.g., "ComfyUI - Personal Laptop")
- Monitor your API key usage in the Isekai dashboard
- Consider using different API keys for different purposes

## Troubleshooting

### Node doesn't appear in ComfyUI

1. Check that the folder is in `ComfyUI/custom_nodes/isekai-comfy-node/`
2. Verify structure matches the new modular format (see Development section)
3. Install dependencies: `pip install -r requirements.txt`
4. Restart ComfyUI completely
5. Check the ComfyUI console for error messages

### "ModuleNotFoundError: No module named 'PIL'"

Install dependencies:

```bash
pip install -r requirements.txt
```

### "Failed to connect to Isekai API"

1. Check your internet connection
2. Verify the API URL is correct (default: `https://api.isekai.sh`)
3. If using local development, ensure `ISEKAI_API_URL` is set correctly
4. Check if your firewall is blocking the connection

### Upload succeeds but image doesn't appear

1. Log in to your Isekai dashboard
2. Navigate to the **"Review"** section
3. Your upload should appear with status "review"
4. Approve the upload to make it visible

### Ollama Summarizer not working

1. Verify Ollama is installed: `ollama --version`
2. Start Ollama server: `ollama serve`
3. Check server is running: `curl http://localhost:11434/api/tags`
4. Ensure model is pulled: `ollama pull llama3`
5. Check URL in node matches Ollama server (default: http://localhost:11434)

### Dynamic String returns empty

1. Check that text_list contains non-empty lines
2. Verify seed value is valid (0 to 2^64-1)
3. Ensure input is multiline (use Shift+Enter in text field)

### Tag Selector returns default value

1. Verify trigger word matches a key in presets (case-insensitive)
2. Check preset format: each line should be "TriggerWord: tags, here"
3. Ensure lines contain colon (`:`) separator

### API Key Not Working / "No API key provided" Error

1. **Check if environment variable is set:**

   ```bash
   # macOS/Linux
   echo $ISEKAI_API_KEY

   # Windows (PowerShell)
   echo $env:ISEKAI_API_KEY

   # Windows (Command Prompt)
   echo %ISEKAI_API_KEY%
   ```

2. **If empty, set the environment variable:**

   - Follow instructions in "Setting Up API Key" section
   - Restart ComfyUI after setting the variable

3. **Verify the key format:**

   - Must start with `isk_`
   - Must have 64 hexadecimal characters after the prefix
   - Example: `isk_0123456789abcdef...` (total 68 characters)

4. **Check console output:**

   - Look for: `[Isekai] Using API key from ISEKAI_API_KEY environment variable`
   - Or: `[Isekai] Using API key from node input`
   - This tells you which method is being used

5. **Fallback to node input:**
   - If environment variable doesn't work, enter key directly in the node
   - Make sure the `api_key` field is not empty

## Rate Limits

- **100 uploads per 15 minutes** per API key
- Exceeding this limit will result in a temporary block
- Wait 15 minutes before trying again
- Monitor your usage in the Isekai dashboard

## File Size Limits

- **Maximum file size:** 50 MB per image
- **Supported formats:** Images are automatically encoded as PNG for upload
- Large images may take longer to upload

## Storage Quotas

Check your current usage in the Isekai dashboard.

## Support

- **Issues:** Report bugs on [GitHub Issues](https://github.com/isekai-sh/isekai-comfy-node/issues)

## Development

### Project Structure

```
isekai-comfy-node/
├── __init__.py          # Package entry point
├── config.py            # Configuration management
├── README.md            # This file
├── requirements.txt     # Dependencies
├── .gitignore           # Git ignore rules
│
├── nodes/               # Node implementations
│   ├── __init__.py
│   ├── base.py          # Base classes and exceptions
│   ├── upload_node.py   # Isekai Upload (with compression)
│   ├── compress_and_save_node.py # Isekai Compress and Save
│   ├── dynamic_string_node.py
│   ├── concatenate_string_node.py
│   ├── tag_selector_node.py
│   ├── ollama_summarizer_node.py
│   ├── round_robin_node.py
│   └── load_text_node.py
│
└── utils/               # Shared utilities
    ├── __init__.py
    ├── validation.py    # Input validation
    ├── image_utils.py   # Image processing
    └── ollama_client.py # Ollama API client
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
