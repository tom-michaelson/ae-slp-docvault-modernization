| File Type              | Extension       | Description                             |
| ---------------------- | --------------- | --------------------------------------- |
| PDF                    | `.pdf`          | Portable Document Format files          |
| Microsoft Word         | `.docx`         | Word documents (Office 2007+)           |
| Microsoft PowerPoint   | `.pptx`         | PowerPoint presentations (Office 2007+) |
| Microsoft Excel        | `.xlsx`         | Excel spreadsheets (Office 2007+)       |
| Microsoft Excel Legacy | `.xls`          | Excel spreadsheets (Office 97-2003)     |
| HTML                   | `.html`, `.htm` | Web pages and HTML documents            |
| CSV                    | `.csv`          | Comma-separated values files            |
| EPUB                   | `.epub`         | Electronic publication files            |
| Outlook                | `.msg`          | Microsoft Outlook message files         |

**Note**: Plain text files (`.txt`, `.md`, `.json`, `.xml`, `.log`, `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.h`, `.go`, `.rs`, `.sh`, `.yaml`, `.yml`, `.toml`, `.ini`, `.cfg`, `.conf`) are returned as-is without parsing.

> **Cross-Platform Compatibility Note**: Due to dependency constraints with the underlying MarkItDown library, the AWA framework uses a curated set of document format parsers to ensure compatibility across Windows, Mac, and Linux environments. The `magika` file type detection library (which depends on `onnxruntime`) has been excluded to avoid platform-specific installation issues.
> EOF < /dev/null
