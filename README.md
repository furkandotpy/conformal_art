# conformal_art

Your JPEG thought it was safe on the real line. **Wrong.** We promote it to the complex plane, hit it with an analytic function, and ask politely for its preimage. What comes back is art, or chaos, or both—depending on how badly you chose `f(z)`.

Heavily inspired by [3Blue1Brown](https://www.youtube.com/c/3blue1brown)'s Escher / conformal-mapping rabbit hole. If that video broke your brain in a good way, this app is here to break your **photos** the same way.

## What it does (the sales pitch)

- Type something obnoxious like `z**2` or `exp(z)` and watch the grid **morph** from “boring identity” to “the complex plane after a few drinks.”
- Load an image. Click the button that promises transformation. **Mathematics happens.** Your pixels get remapped through an approximate inverse map because nobody invited a closed-form branch cut to this party.
- Save the result and pretend you meant it.

## What it does *not* do

- Guarantee museum-grade numerical analysis. This is a playground, not a PhD thesis defense.
- Respect your aspect ratio’s feelings. It tries; read the code if you’re picky.

## Running it

You’ll want a Python env and the usual suspects: **PyQt6**, **matplotlib**, **NumPy**, **Pillow**, **SymPy**. Then:

```bash
python -m src.main
```

(or `python src/main.py` from the repo root—your shell, your funeral.)

## License

Apache 2.0—see `LICENSE`. Fork it, sass it back, ship a screensaver, we’re not your supervisor.
