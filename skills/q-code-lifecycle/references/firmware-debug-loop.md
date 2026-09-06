# Firmware Debug Loop Checklist

Use this checklist when a code change will be compiled, flashed and verified on
physical hardware. It describes a general method; device-specific commands,
register values, board wiring and test limits belong in the project record.

## Define the checkpoint

- Translate the requested sequence into checkpoints, such as one channel,
  another channel, then simultaneous operation.
- Make the runtime default match the next agreed physical test. Keep later
  modes disabled until their prerequisite checks pass.
- Distinguish implementation, successful compilation and observed hardware
  behavior. None of these alone proves the other two.
- Confirm test duration, operating limits and a stop procedure before any
  automated command that can energize an actuator.

## Preserve a known-good state

- Record the source commit, local changes, selected configuration and exact
  image before a risky edit. Do not assume the remote branch matches the
  operator's working hardware setup.
- Keep comment-only changes separate from executable changes.
- Identify the intended state-machine, sampling, output, pin-routing and build
  surfaces before editing. Inspect partial changes if an edit fails midway.

## Build and flash

- Check the selected mode in source and prefer a clean build after changing
  generated configuration or build metadata.
- Record dependencies on ignored generated files. Update tracked project
  metadata before claiming the build is reproducible elsewhere.
- Discover probes without writing to the target. Resolve ambiguity before
  selecting a probe and verify the exact target device in the installed tools.
- State the image, probe, target, erase scope and reset behavior before flash.
  Never substitute a nearby device definition merely to bypass an error.
- Verify reset and run state using the documented procedure for that target.
  A successful download alone does not prove the program is running.

## Observe the complete signal path

- Separate firmware symbols, debug transport exposure, host project metadata
  and the running host application's cache. A variable in source is not
  automatically visible or writable in the host interface.
- Validate edited project files with their format parser, reload them and
  read back the intended variables. Preserve ownership and object references
  when cloning or extending a host project.
- Verify signal routing against the board documentation and generated setup.
  Compare requested output, computed values, register readback and physical
  measurement rather than relying on a single state flag.
- For buffered peripheral updates, confirm when values are staged and when a
  coordinated update becomes active. For shared sampling resources, confirm
  channel ownership and timing before changing the control algorithm.
- Keep logical channel names distinct from schematic labels. Record polarity,
  phase order and resource ownership in the private project evidence.

## Run bounded automation

- Verify the host tool's documented protocol, version and connection state.
  Probe supported read operations before planning writes.
- Use verified symbolic variables where supported. Check data widths and
  treat transport errors or rejected results as failures, not measurements.
- Use an explicit setup, stimulus, sampling and cleanup sequence. Put the
  stop action in a guaranteed cleanup path and retain an independent physical
  stop method; software cleanup cannot guarantee a stop after connection loss.
- Log every write and read back its result. Do not increase operating limits
  or switch control modes beyond the agreed test.
- Validate each channel and the required simultaneous cases before promoting
  a multi-channel mode. Confirm limits from the actual device and application;
  do not reuse numbers from an unrelated demonstration.
- Record whether the automation stopped the test, a fault stopped it, or an
  operator intervened. Keep physical observations separate from script status.

## Handoff and cleanup

- Record configuration, image identity, build and flash results, observed
  behavior, unverified conditions and the next permitted checkpoint.
- Inspect Git changes after builds and tool runs. Keep generated logs and
  machine-specific project state separate from reproducible source.
- Use explicit text encoding, check diffs and parse structured files after
  scripted edits. Avoid blind replacement across shared fields and instance
  names when adding channels.
- Reproduce the checkpoint from its documented inputs before promoting it to
  a reusable release. Generalize lessons before publishing them; retain board
  details and measurements only in the appropriately scoped project record.
