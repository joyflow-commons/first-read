# Field notes: reading a PDF book by hand

First Read does not import PDFs. These notes record what happened when one of
its authors read the opening chapters of a novel from a PDF anyway, using
`pdftotext` and a hand-kept reading journal with a protected cursor. They are
here because the failures are the specification for the eventual importer, and
because other companions will try the same thing.

## What went wrong

Three of the first five chapters had an accidental exposure. None was
deliberate, and each came from locating the next chapter the convenient way.

1. **Trusting an old extraction's line position.** On resuming, the reader
   reused a line offset from a previous temporary extraction. It landed in the
   middle of the chapter and ran into the opening of the one after before the
   real boundary was recognized.
2. **Extracting a page range that was too wide.** A generous page range was
   pulled "to be safe" and then narrowed. The wide output had already shown a
   later passage, including character names that had not been introduced.
3. **Stopping at the page instead of the chapter.** A chapter ended partway
   down a page and the next began immediately beneath it. Reading to the end
   of the page exposed the next chapter's opening.

## What worked

The fourth attempt was clean and has stayed clean since:

1. Convert the whole PDF to a text file once, in a fresh temporary directory,
   without printing any of it.
2. Search that file for **structural lines only**: lines that consist of
   nothing but a chapter number or a part heading. Print line numbers and
   those bare lines, never neighboring prose. A table of contents will match
   too; the body matches come after it.
3. Read exactly from the current chapter's line to the line before the next
   structural match. If the last line looks cut off, read one more line at a
   time, never a block.
4. Record the cursor as part, chapter, and "next", not as a page or line
   number. Line numbers do not survive a new extraction.
5. Delete the extraction afterwards so there is no loose full text to stumble
   into later.

## Keep an honest exposure receipt

Each journal entry began with a short receipt saying whether the chapter was
read cleanly and, if not, exactly what was seen early. This mattered more than
expected. A spoiled detail cannot be unseen, but naming it stops the reader
from later presenting a reaction as a sealed first encounter when it was not.
The same idea is built into First Read as prior-exposure receipts.

## What this means for the importer

- Boundaries must come from structure, not from pages or remembered offsets.
- A reveal must end at the authored boundary even when the page continues.
- Preflight must never print prose around a boundary to help locate it.
- Chapter titles and character names in a table of contents are exposure too;
  structural search should return positions, not text, wherever it can.
