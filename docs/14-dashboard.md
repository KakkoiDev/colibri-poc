# Using the lab dashboard

Open http://127.0.0.1:8766. The three main pages follow the everyday tasks.

```mermaid
flowchart LR
    A[Models: download a model] --> B[Run benches: choose model and bench]
    B --> C[One click: run or queue]
    C --> D[Running now and Up next]
    D --> E[Results: measured values and answers]
```

## Run benches

Choose a model, a bench and a start condition, then click **Run bench** or
**Add bench to queue** once. The button also resumes a paused queue; its label
says so before you click. The page confirms exactly what was added and prevents
another click on that selection. Use **Select multiple benches** for a campaign.

The plan shows what will run, its estimated duration and how many jobs are ahead.
A partially completed quality bench resumes unfinished answers. **Running now**
shows the active case and progress; expand it to see finished and upcoming cases.
**Up next** lists the first five waiting jobs, their order and any quiet-machine
condition. The queue link opens the full list, logs and reorder controls.
**Recently finished** includes failures as well as successful jobs.

The default condition starts when the GPU is free. The quiet condition waits for
20 GB free for two minutes. Bench types that intrinsically require a quiet run
keep that requirement. Estimates are approximate. Live status refreshes every
five seconds without resetting your model or bench selection.

## Results

Read saved speed, prompt time, expert hit rate and process memory values, then
compare quality scores and generated answers. The speed/RAM/thread link opens
all engine measurements with filtering. Coverage and bench definitions are
collapsed below the measured values. A failed job stays visible in queue history;
it does not become a successful measurement.

## Models

Check installed model folders and their measured disk usage. Available catalog
models retain their download confirmation and progress controls. **Move to Trash**
asks for confirmation and keeps saved benchmark results. The owner's original
model is protected, and an active or downloading model cannot be removed.
Models outside the managed catalog are listed separately.

Advanced navigation keeps the experiment, research and machine tools available.

## Resume an unfinished run

Use **Resume · N remaining** in Recently finished or the full queue history.
It queues the original model, settings and run identity and resumes the queue.
The existing quiet-machine condition is preserved. A bench already queued or
running cannot be queued a second time through Resume.

```mermaid
flowchart LR
    A[Interrupted or failed run] --> B[Resume remaining cases]
    B --> C[Keep successful cases]
    B --> D[Archive failed attempts]
    D --> E[Retry failed or missing cases]
```

Quality benches reuse successful answer files, including answers graded incorrect:
a wrong answer is a measured result, not an execution failure. Failed and malformed
answer records are archived under the run's `attempts/` folder before retrying.
Speed, thread and RAM sweeps reuse successful published cases using a stable
`--run-id`. Previous failed sweep records and logs are copied to
`results/suite-attempts/`. Older sweep jobs use their original launch minute.
Only quality and standard sweep jobs offer Resume; experimental and quiet
campaign commands do not yet have this resume control. The full history currently
shows the latest 25 jobs.
