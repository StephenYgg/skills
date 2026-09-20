# Platform And Output

## Content Modes

### Article

- Target about 800 Chinese characters; use a working range of 650-1100 content units.
- Include 3-4 relevant local images, including the cover when the cover is referenced in the Markdown.
- Develop one thesis with evidence, mechanism, a limitation or counterpoint, and a bounded conclusion.
- Prefer 3-5 meaningful sections rather than many short headings.

### Post

- Target 100-250 Chinese characters.
- Include 1-6 relevant local images.
- Make one claim or observation, provide its strongest support, and state one implication.
- Do not compress an unsupported hot take into the short format.

Count Chinese characters, numbers, and meaningful Latin word groups as content. Exclude Markdown syntax, image alt text, URLs, frontmatter, and the source ledger from the target length.

## Platform Adaptation

Create one evidence base, then adapt the presentation.

For Toutiao:

- Enter the concrete event or reader consequence quickly.
- Keep paragraphs compact and preserve narrative momentum.
- Use an informative hook, not a title that promises more than the evidence supports.
- Make the practical consequence visible without simplifying away the mechanism.

For Baijiahao:

- Name the main entity and topic clearly in the title and opening.
- Use descriptive subheadings that make the reasoning easy to scan.
- State dates, source context, and technical terms precisely.
- Make the final judgment answer the question raised by the title.

Do not claim knowledge of recommendation algorithms or fixed platform limits without current official evidence. When exact title, image, disclosure, or formatting rules matter, check the platform's current official requirements before delivery.

## Markdown Package

Create a dedicated output directory outside the Skill directory:

```text
<date>-<topic-slug>/
├── article.md or post.md
├── evidence.md
├── image-manifest.md
└── assets/
    ├── cover.png
    ├── figure-01.png
    └── figure-02.png
```

When the user requests both platforms, create `toutiao.md` and `baijiahao.md` in the same package. Keep facts consistent while adapting the title, opening, headings, and ending.

Use standard relative Markdown image syntax:

```markdown
![准确说明图片内容的替代文本](assets/figure-01.png)
```

Place each image after the paragraph or heading it supports. Do not use absolute local paths, remote hotlinks, base64 data, missing placeholders, or Obsidian wikilinks in publishable Markdown.

Create `image-manifest.md` with one row per image:

```markdown
| File | Role | Insert after | Origin | Attribution | Generation prompt |
| --- | --- | --- | --- | --- | --- |
| assets/cover.png | Cover | Title | AI-generated | AI-generated illustration | ... |
```

The publishable Markdown should contain the article only. Keep research notes, rejected claims, local source paths, and production instructions in `evidence.md` or `image-manifest.md`.

## Title And Final Checks

- Offer 3 title candidates outside the publishable Markdown when the user has not fixed a title, then select one for the file.
- Choose the title that most accurately expresses the thesis, not the most sensational option.
- Ensure the opening substantiates the title within the first few paragraphs.
- Ensure all referenced image files exist locally.
- Run `scripts/validate_article.py` for every publishable Markdown variant.
