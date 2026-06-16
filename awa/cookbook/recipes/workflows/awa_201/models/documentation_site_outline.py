from pydantic import BaseModel, Field


class DocumentationPage(BaseModel):
    title: str = Field(..., description="Title of the documentation page.")
    path: str = Field(
        ...,
        description=(
            "Full page path and name, e.g. /section/my_page.md. MUST start with a leading slash (/). "
            "All files should be markdown files, ending with '.md'."
        ),
    )
    summary: str = Field(
        ...,
        description=(
            "Detailed summary of the page's content, including suggested section headers, in markdown format. "
            "Use brief bullet lists to summarize what content should be in each section."
        ),
    )
    source_files: list[str] = Field(
        ...,
        description=(
            "List of TOP FIVE source file paths relevant to this documentation page. Should be RELATIVE paths, "
            "relative to the root folder of the project. IMPORTANT: Only include the MOST IMPORTANT five files, "
            "not every single related file. Pick the files that are most relevant to the content of this page."
        ),
    )
    linked_pages: list[str] = Field(
        ...,
        description=(
            "List of other documentation page paths this page should link to. Values MUST match the 'path' "
            "property of other pages in this outline. Can reference pages in other sections."
        ),
    )


class DocumentationSection(BaseModel):
    title: str = Field(..., description="Sentence-case title of the section.")
    name: str = Field(
        ...,
        pattern=r"^[a-z0-9_]+$",
        description="Snake-case name of the section, used as the folder path on disk.",
    )
    pages: list[DocumentationPage] = Field(..., description="Pages directly under this section.")
    sections: list["DocumentationSection"] = Field(default_factory=list, description="Nested subsections.")


class DocumentationSiteOutline(BaseModel):
    sections: list[DocumentationSection] = Field(..., description="Top-level sections of the documentation site.")


# Rebuild the model to handle the recursive Section reference
DocumentationSection.model_rebuild()
