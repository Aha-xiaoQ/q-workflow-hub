# Install whisper.cpp Provider

Use this workflow to make the `whisper-cpp` engine reproducible instead of
depending on temporary files under `%TEMP%`.

## Goal

End with two stable local paths:

- `WHISPER_CPP_CLI`: path to `whisper-cli.exe`
- `WHISPER_CPP_MODEL`: path to a ggml model such as `ggml-small.bin`

Do not commit binaries, model files, private audio, or downloaded archives to
the repository.

## Recommended Windows Layout

Keep tools and models outside the Git repository:

```powershell
$WhisperRoot = "$env:LOCALAPPDATA\Programs\whisper.cpp"
$WhisperBin = "$WhisperRoot\bin"
$WhisperModels = "$env:LOCALAPPDATA\Models\whisper.cpp"
New-Item -ItemType Directory -Force -Path $WhisperBin, $WhisperModels
```

## Route A: Official CPU Smoke Path

Use this route when you need a stable baseline quickly.

1. Download a Windows release archive from the official `ggml-org/whisper.cpp`
   releases page.
2. Extract the archive and copy `whisper-cli.exe` plus its runtime DLLs into
   `$WhisperBin`.
3. Download a ggml model from the official Hugging Face model repository, such
   as `ggml-base.bin` or `ggml-small.bin`, into `$WhisperModels`.
4. Record the asset names and SHA256 hashes in your project or personal state
   if you need machine-to-machine reproducibility:

   ```powershell
   Get-FileHash "$WhisperBin\whisper-cli.exe" -Algorithm SHA256
   Get-FileHash "$WhisperModels\ggml-small.bin" -Algorithm SHA256
   ```

## Route B: Windows AMD/Vulkan Path

Use this route for AMD GPU acceleration on Windows.

Official Windows release assets may not include a Vulkan build. For a durable
AMD route, prefer one of these options:

- build `whisper.cpp` from source with the Vulkan backend enabled;
- use an internally pinned binary artifact whose source, version, license, and
  SHA256 hash are recorded.

Minimum setup checklist:

- AMD driver with Vulkan support installed;
- `vulkaninfo --summary` can see the GPU;
- CMake and Visual Studio Build Tools are installed when building locally;
- `whisper-cli.exe --help` prints a `ggml_vulkan` device line.

Validation command:

```powershell
& "$WhisperBin\whisper-cli.exe" --help | Select-String -Pattern "ggml_vulkan|Vulkan|device"
```

If the CLI cannot see Vulkan, do not mark the AMD path ready. Fall back to the
official CPU route or `faster-whisper` CPU while you fix the local install.

## Configure q-audio-intake

For the current shell:

```powershell
$env:WHISPER_CPP_CLI = "$WhisperBin\whisper-cli.exe"
$env:WHISPER_CPP_MODEL = "$WhisperModels\ggml-small.bin"
```

For future shells:

```powershell
[Environment]::SetEnvironmentVariable("WHISPER_CPP_CLI", "$WhisperBin\whisper-cli.exe", "User")
[Environment]::SetEnvironmentVariable("WHISPER_CPP_MODEL", "$WhisperModels\ggml-small.bin", "User")
```

Then verify:

```powershell
python skills\q-audio-intake\scripts\q_audio_intake.py check-env
```

The `whisper_cpp_cli` and `whisper_cpp_model` checks should both be `OK`.

## Smoke Test

Use a short local audio file first:

```powershell
python skills\q-audio-intake\scripts\q_audio_intake.py transcribe `
  --input "<short-audio.mp3>" `
  --engine whisper-cpp `
  --language zh `
  --output-dir "local-state/q-audio-intake/whisper-cpp-smoke"
```

Expected outputs:

- `metadata.json`
- `transcript.txt`
- `whisper_cpp.json`
- `whisper_cpp_output.txt`
- `whisper_cpp_output.json`
- `logs/whisper_cpp.stdout.txt`
- `logs/whisper_cpp.stderr.txt`

## Benchmark Before Promotion

Do not make `whisper-cpp` the default provider from a smoke test alone.
Benchmark it against a reference subtitle segment:

```powershell
python skills\q-audio-intake\scripts\q_audio_intake.py score `
  --reference "<gold-segment.txt>" `
  --candidate "local-state/q-audio-intake/whisper-cpp-smoke/transcript.txt" `
  --metric auto `
  --output-dir "local-state/q-audio-intake/whisper-cpp-smoke"
```

Record runtime and CER/WER before recommending a model as the default.

## Current Xiao Q Baseline

On the 300s-480s Bilibili Chinese tutorial clip:

- `faster-whisper small` CPU: CER `0.086907`, runtime `61.279s`.
- `whisper.cpp` Vulkan `ggml-small` on RX 6650 XT: CER `0.120767`, runtime
  about `7.2s`.

Interpretation: `whisper.cpp` Vulkan is currently a strong fast-draft route,
not the highest-quality Chinese tutorial transcript route.
