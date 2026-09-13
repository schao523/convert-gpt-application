# Third-party notices

## Scripture corpus and derived index

The publisher represents the two exact hash-identified Chinese Union Version PDFs in `THIRD_PARTY_CONTENT.md` as public domain and authorizes their redistribution. The immutable `cuv.sqlite3` corpus and `cuv-rag-index.sqlite3` semantic index are deterministic derivatives of that represented public-domain text. Source attribution is preserved for provenance and does not imply endorsement.

The OpenClaw artifact keeps `cuv.sqlite3` locally and identifies the larger PDF/index archives by immutable URL, size, SHA-256, and per-member SHA-256. Downloading them does not change their public-domain content classification or make them shared assets among plugins.

## Bundled RAG subsystem

`vendor/rag-subsystem/rag_subsystem-0.2.1-py3-none-any.whl` is built from the pinned RAGenius `rag_subsystem` source commit recorded in its adjacent manifest. It is distributed under the MIT License. Copyright and license terms from that project remain applicable.

## Embedding model

The optional `BAAI/bge-large-zh-v1.5` model is not bundled. `setup-rag` downloads only revision `79e7739b6ab944e86d6171e44d24c997fc1e0116` using the file URLs and SHA-256 values in `vendor/rag-runtime/model-manifest.json`. The model declares the MIT License. BAAI, FlagEmbedding, and Hugging Face do not endorse this plugin.

## Hash-locked runtime dependency inventory

The following packages may be installed into the user's private runtime according to platform and Python-version markers in `requirements-rag.lock`. Their upstream copyright and license terms remain applicable; pip installs their package metadata and license files into the private environment. This generated inventory is part of the release lock and must be regenerated when that lock changes.

```text
annotated-doc 0.0.5
anyio 4.14.2
certifi 2026.7.22
click 8.4.2
colorama 0.4.6
exceptiongroup 1.3.1
filelock 3.32.4
fsspec 2026.7.0
h11 0.16.0
hf-xet 1.6.0
httpcore 1.0.9
httpx 0.28.1
huggingface-hub 1.28.0
idna 3.19
jinja2 3.1.6
joblib 1.5.3
markdown-it-py 4.2.0
markupsafe 3.0.3
mdurl 0.1.2
mpmath 1.3.0
narwhals 2.25.0
networkx 3.4.2 / 3.6.1
numpy 2.2.6 / 2.4.6 / 2.5.2
packaging 26.3
pygments 2.21.0
pyyaml 6.0.3
regex 2026.7.19
rich 15.0.0
safetensors 0.8.0
scikit-learn 1.7.2 / 1.9.0
scipy 1.15.3 / 1.17.1 / 1.18.1
sentence-transformers 5.7.0
setuptools 84.0.0
shellingham 1.5.4
sympy 1.14.0
threadpoolctl 3.6.0
tokenizers 0.22.2
torch 2.13.0 / 2.13.0+cpu
tqdm 4.70.0
transformers 5.15.1
typer 0.27.1
typing-extensions 4.16.0
```

The plugin code itself is MIT-licensed. External Poppler, Tesseract, and `chi_tra` authoring tools are not bundled and retain their own terms.
