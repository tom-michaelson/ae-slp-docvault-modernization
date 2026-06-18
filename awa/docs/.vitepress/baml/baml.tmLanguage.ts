const bamlJinjaTextmate = {
  name: "baml-jinja",
  scopeName: "source.baml-jinja",
  // comment: "Jinja Templates",
  foldingStartMarker: "({%\\s*(block|filter|for|if|macro|raw))",
  foldingStopMarker:
    "({%\\s*(endblock|endfilter|endfor|endif|endmacro|endraw)\\s*%})",
  patterns: [
    {
      begin: "({%)\\s*(raw)\\s*(%})",
      captures: {
        1: {
          name: "storage.type.jinja.delimiter.tag",
        },
        2: {
          name: "keyword.control.jinja",
        },
        3: {
          name: "storage.type.jinja.delimiter.tag",
        },
      },
      end: "({%)\\s*(endraw)\\s*(%})",
      name: "comment.block.jinja.raw",
    },
    {
      include: "#comments",
    },
    {
      begin: "{{-?",
      captures: {
        0: {
          name: "storage.type.jinja.delimiter",
        },
      },
      end: "-?}}",
      name: "variable.meta.scope.jinja",
      patterns: [
        {
          include: "#expression",
        },
      ],
    },
    {
      begin: "{%-?",
      captures: {
        0: {
          name: "storage.type.jinja.delimiter",
        },
      },
      end: "-?%}",
      name: "meta.scope.jinja.tag",
      patterns: [
        {
          include: "#expression",
        },
      ],
    },
  ],
  repository: {
    comments: {
      begin: "{#-?",
      captures: {
        0: {
          name: "storage.type.jinja.delimiter",
        },
      },
      end: "-?#}",
      name: "comment.block.jinja",
      patterns: [
        {
          include: "#comments",
        },
      ],
    },
    escaped_char: {
      match: "\\\\x[0-9A-F]{2}",
      name: "constant.character.escape.hex.jinja",
    },
    escaped_unicode_char: {
      captures: {
        1: {
          name: "constant.character.escape.unicode.16-bit-hex.jinja",
        },
        2: {
          name: "constant.character.escape.unicode.32-bit-hex.jinja",
        },
        3: {
          name: "constant.character.escape.unicode.name.jinja",
        },
      },
      match:
        "(\\\\U[0-9A-Fa-f]{8})|(\\\\u[0-9A-Fa-f]{4})|(\\\\N\\{[a-zA-Z ]+\\})",
    },
    expression: {
      patterns: [
        {
          captures: {
            1: {
              name: "keyword.control.jinja",
            },
            2: {
              name: "variable.other.jinja.block",
            },
          },
          match: "\\s*\\b(block)\\s+([a-zA-Z_][a-zA-Z0-9_]*)\\b",
        },
        {
          captures: {
            1: {
              name: "keyword.control.jinja",
            },
            2: {
              name: "variable.other.jinja.filter",
            },
          },
          match: "\\s*\\b(filter)\\s+([a-zA-Z_][a-zA-Z0-9_]*)\\b",
        },
        {
          captures: {
            1: {
              name: "keyword.control.jinja",
            },
            2: {
              name: "variable.other.jinja.test",
            },
          },
          match: "\\s*\\b(is)\\s+([a-zA-Z_][a-zA-Z0-9_]*)\\b",
        },
        {
          captures: {
            1: {
              name: "keyword.control.jinja",
            },
          },
          match:
            "(?<=\\{\\%-|\\{\\%)\\s*\\b([a-zA-Z_][a-zA-Z0-9_]*)\\b(?!\\s*[,=])",
        },
        {
          match:
            "\\b(and|else|if|in|import|not|or|recursive|with(out)?\\s+context)\\b",
          name: "keyword.control.jinja",
        },
        {
          match: "\\b(true|false|none)\\b",
          name: "constant.language.jinja",
        },
        {
          match: "\\b(loop|super|self|varargs|kwargs)\\b",
          name: "variable.language.jinja",
        },
        {
          match: "[a-zA-Z_][a-zA-Z0-9_]*",
          name: "variable.other.jinja",
        },
        {
          match: "(\\+|\\-|\\*\\*|\\*|//|/|%)",
          name: "keyword.operator.arithmetic.jinja",
        },
        {
          captures: {
            1: {
              name: "punctuation.other.jinja",
            },
            2: {
              name: "variable.other.jinja.filter",
            },
          },
          match: "(\\|)([a-zA-Z_][a-zA-Z0-9_]*)",
        },
        {
          captures: {
            1: {
              name: "punctuation.other.jinja",
            },
            2: {
              name: "variable.other.jinja.attribute",
            },
          },
          match: "(\\.)([a-zA-Z_][a-zA-Z0-9_]*)",
        },
        {
          begin: "\\[",
          captures: {
            0: {
              name: "punctuation.other.jinja",
            },
          },
          end: "\\]",
          patterns: [
            {
              include: "#expression",
            },
          ],
        },
        {
          begin: "\\(",
          captures: {
            0: {
              name: "punctuation.other.jinja",
            },
          },
          end: "\\)",
          patterns: [
            {
              include: "#expression",
            },
          ],
        },
        {
          begin: "\\{",
          captures: {
            0: {
              name: "punctuation.other.jinja",
            },
          },
          end: "\\}",
          patterns: [
            {
              include: "#expression",
            },
          ],
        },
        {
          match: "(\\.|:|\\||,)",
          name: "punctuation.other.jinja",
        },
        {
          match: "(==|<=|=>|<|>|!=)",
          name: "keyword.operator.comparison.jinja",
        },
        {
          match: "=",
          name: "keyword.operator.assignment.jinja",
        },
        {
          begin: '"',
          beginCaptures: {
            0: {
              name: "punctuation.definition.string.begin.jinja",
            },
          },
          end: '"',
          endCaptures: {
            0: {
              name: "punctuation.definition.string.end.jinja",
            },
          },
          name: "string.quoted.double.jinja",
          patterns: [
            {
              include: "#string",
            },
          ],
        },
        {
          begin: "'",
          beginCaptures: {
            0: {
              name: "punctuation.definition.string.begin.jinja",
            },
          },
          end: "'",
          endCaptures: {
            0: {
              name: "punctuation.definition.string.end.jinja",
            },
          },
          name: "string.quoted.single.jinja",
          patterns: [
            {
              include: "#string",
            },
          ],
        },
        {
          begin: "@/",
          beginCaptures: {
            0: {
              name: "punctuation.definition.regexp.begin.jinja",
            },
          },
          end: "/",
          endCaptures: {
            0: {
              name: "punctuation.definition.regexp.end.jinja",
            },
          },
          name: "string.regexp.jinja",
          patterns: [
            {
              include: "#simple_escapes",
            },
          ],
        },
      ],
    },
    simple_escapes: {
      captures: {
        1: {
          name: "constant.character.escape.newline.jinja",
        },
        2: {
          name: "constant.character.escape.backlash.jinja",
        },
        3: {
          name: "constant.character.escape.double-quote.jinja",
        },
        4: {
          name: "constant.character.escape.single-quote.jinja",
        },
        5: {
          name: "constant.character.escape.bell.jinja",
        },
        6: {
          name: "constant.character.escape.backspace.jinja",
        },
        7: {
          name: "constant.character.escape.formfeed.jinja",
        },
        8: {
          name: "constant.character.escape.linefeed.jinja",
        },
        9: {
          name: "constant.character.escape.return.jinja",
        },
        10: {
          name: "constant.character.escape.tab.jinja",
        },
        11: {
          name: "constant.character.escape.vertical-tab.jinja",
        },
      },
      match:
        "(\\\\\\n)|(\\\\\\\\)|(\\\\\\\")|(\\\\')|(\\\\a)|(\\\\b)|(\\\\f)|(\\\\n)|(\\\\r)|(\\\\t)|(\\\\v)",
    },
    string: {
      patterns: [
        {
          include: "#simple_escapes",
        },
        {
          include: "#escaped_char",
        },
        {
          include: "#escaped_unicode_char",
        },
      ],
    },
  },
};

const bamlTextmate = {
  fileTypes: ["baml"],
  name: "baml",
  embeddedLangs: ["baml-jinja"],
  patterns: [{ include: "#comment" }, { include: "#schema" }],
  repository: {
    schema: {
      patterns: [
        { include: "#enum_declaration" },
        { include: "#interface_declaration" },
        { include: "#template_string_declaration" },
        { include: "#function_declaration" },
        { include: "#config_block" },
        { include: "#type_alias" },
        { include: "#function" },
        { include: "#language_block_python" },
        { include: "#language_block_ts" },
        { include: "#language_block_jinja" },
      ],
    },
    comment: {
      patterns: [
        {
          name: "comment.line",
          match: "//.*",
        },
        {
          name: "comment.block.documentation",
          begin: "///",
          end: "$",
          patterns: [
            {
              name: "comment.block.documentation",
              match: ".*",
            },
          ],
        },
        {
          include: "#curly_comment",
        },
      ],
    },

    enum_declaration: {
      begin: "(enum)\\s+(\\w+)",
      beginCaptures: {
        1: { name: "storage.type.enum" },
        2: { name: "entity.name.type" },
      },
      end: "\\}",
      patterns: [
        { include: "#comment" },
        { include: "#block_attribute" },
        {
          name: "variable.other.field",
          match: "\\b[A-Za-z_][A-Za-z0-9_]*\\b",
        },
      ],
    },
    interface_declaration: {
      begin: "(class|override)\\s+(\\w+)\\s*\\{",
      beginCaptures: {
        1: { name: "storage.type.declaration.interface" },
        2: { name: "entity.name.type" },
      },
      end: "\\}",
      patterns: [
        { include: "#comment" },
        {
          // comment: "Property + Type",
          begin: "(\\w+)",
          beginCaptures: {
            "1": { name: "variable.other.readwrite.interface" },
          },
          end: "(?=$|\\n|@|\\}|/)",
          patterns: [{ include: "#type_definition" }],
        },
        { include: "#block_attribute" },
      ],
    },
    template_string_declaration: {
      begin: "(template_string)\\s+(\\w+)",
      beginCaptures: {
        1: { name: "storage.type.declaration.function" },
        2: { name: "entity.name.function" },
      },
      end: '(")(#)',
      endCaptures: {
        1: { name: "string.quoted.block.baml" },
        2: { name: "string.quoted.block.baml" },
      },
      name: "string.quoted.block.baml",
      patterns: [
        { include: "#comment" },
        { include: "#function_parameters" },
        { include: "#block_string" },
      ],
    },
    function_declaration: {
      // comment: "Function declaration",
      begin: "(function)\\s+(\\w+)",
      beginCaptures: {
        1: { name: "storage.type.declaration.function" },
        2: { name: "entity.name.function" },
      },
      end: "\\}",
      patterns: [
        { include: "#comment" },
        { include: "#function_parameters" },
        { include: "#arrow_return_type" },
        { include: "#function_body" },
      ],
    },
    function_parameters: {
      begin: "\\(",
      end: "\\)",
      patterns: [{ include: "#comment" }, { include: "#function_name_type" }],
    },
    function_name_type: {
      patterns: [
        {
          match: "(\\w+)\\s*:",
          captures: {
            1: { name: "variable.other.readwrite.function_name" },
          },
        },
        {
          include: "#type_definition",
        },
      ],
    },
    type_definition: {
      patterns: [
        {
          match: "\\b(bool|int|float|string|null|image|audio)\\b",
          name: "storage.type.baml",
        },
        {
          begin: "(map)\\s*<",
          beginCaptures: {
            1: { name: "storage.type.baml" },
          },
          patterns: [
            { include: "#type_definition" },
            { include: "#type_definition" },
          ],
          end: ">",
        },
        {
          match: "\\b(true|false)\\b",
          name: "constant.language.boolean",
        },
        {
          match: "\\w+",
          name: "support.type",
        },
        {
          include: "#string_literal",
        },
        {
          match: "\\[\\]",
          name: "keyword.control.baml",
        },
        {
          match: "\\?",
          name: "keyword.control.baml",
        },
        {
          // comment: "union a | b | c",
          match: "\\|",
          name: "keyword.control.baml",
        },
        {
          // comment: "Groups",
          begin: "\\(",
          beginCaptures: {
            "0": { name: "keyword.control" },
          },
          end: "(\\))(\\[\\])*(\\?)?",
          endCaptures: {
            1: { name: "keyword.control" },
            2: { name: "keyword.control" },
            3: { name: "keyword.control" },
          },
          patterns: [{ include: "#type_definition" }],
        },
      ],
    },
    arrow_return_type: {
      begin: "(?<=\\))\\s*(->)\\s*",
      beginCaptures: {
        1: { name: "keyword.control.baml.arrow" },
      },
      end: "(?=\\{)",
      patterns: [
        {
          include: "#comment",
        },
        {
          include: "#type_definition",
        },
      ],
    },
    function_body: {
      begin: "(?<=\\{)\\s*",
      end: "(?=\\})",
      patterns: [
        { include: "#comment" },
        { include: "#block_attribute" },
        {
          // comment: "Function client properties",
          patterns: [
            {
              match: '(client)\\s+(\\w+|"[^"]*")',
              captures: {
                1: { name: "variable.other.readwrite.client" },
                2: {
                  patterns: [
                    {
                      match: "\\w+",
                      name: "entity.name.other.client",
                    },
                    { include: "#string_literal" },
                  ],
                },
              },
              name: "meta.client.declaration",
            },
            {
              begin: '\\s+(prompt)\\s+(#{1,5})(")',
              beginCaptures: {
                1: { name: "variable.other.readwrite.prompt" },
                2: { name: "string.quoted.block.baml.prompt" },
                3: { name: "string.quoted.block.baml.prompt" },
              },
              end: '\\s*("\\2)',
              contentName: "string.quoted.block.baml.prompt",
              endCaptures: {
                "0": { name: "string.quoted.block.baml.prompt" },
              },
              patterns: [{ include: "source.baml-jinja" }],
            },
          ],
        },
      ],
    },
    key_value_pair: {
      begin: "(\\w+)\\s*",
      beginCaptures: {
        "1": { name: "variable.other.readwrite.key_value_pair" },
      },
      end: "(?=\\n)",
      patterns: [{ include: "#string_literal" }],
    },
    function_declaration2: {
      begin:
        "(function)\\s+(\\w+)\\(([^)]*)\\)\\s*(->)\\s*([\\w\\s\\[\\]|,?]+)\\s+\\{",
      beginCaptures: {
        1: { name: "storage.type.declaration.function" },
        2: { name: "entity.name.function" },
        3: { name: "variable.parameter.function" },
        4: { name: "keyword.operator" },
        5: { name: "support.type" },
      },
      end: "\\}",
      patterns: [
        { include: "#comment" },
        {
          match: '(client)\\s+(\\w+|"[^"]*")',
          captures: {
            1: { name: "variable.other.readwrite.client" },
            2: {
              patterns: [
                {
                  match: "\\w+",
                  name: "entity.name.other.client",
                },
                { include: "#string_literal" },
              ],
            },
          },
          name: "meta.client.declaration",
        },
        {
          begin: '\\s+(prompt)\\s+(#"){1,3}',
          beginCaptures: {
            1: { name: "variable.other.readwrite.prompt" },
            2: { name: "string.quoted.block.baml.prompt" },
          },
          end: '\\s*("#)',
          contentName: "string.quoted.block.baml.prompt",
          endCaptures: {
            1: { name: "string.quoted.block.baml.prompt" },
          },
          patterns: [{ include: "source.baml-jinja" }],
        },
        { include: "#block_attribute" },
      ],
    },

    keyword: {
      patterns: [
        {
          match: "\\b(input|output)\\b",
          name: "keyword.special.input-output",
        },
      ],
    },
    single_variable_no_assignment: {
      match: "^\\s*\\w+\\b",
      name: "variable.other.readwrite.single_var",
    },
    config_block: {
      begin:
        "(client|generator|retry_policy|printer|test)\\s*(<([^>]+)>)?\\s+(\\w+)\\s*\\{",
      beginCaptures: {
        1: { name: "storage.type.declaration" },
        3: { name: "storage.type.declaration" },
        4: { name: "entity.name.type" },
      },
      end: "\\}",
      patterns: [
        { include: "#comment" },
        { include: "#block_attribute" },
        { include: "#property_assignment_expression" },
      ],
    },
    block_attribute: {
      patterns: [
        {
          begin: "(@{1,2}(?:check|assert))\\(([^,]+)?\\s*,\\s*()",
          beginCaptures: {
            1: { name: "entity.name.function.attribute" },
            2: { name: "variable.parameter.checkName" },
            3: { name: "punctuation.definition.template-expression.begin" },
          },
          end: "()\\)",
          endCaptures: {
            "1": { name: "punctuation.definition.template-expression.end" },
          },
          contentName: "string.quoted.block.thing",
          patterns: [{ include: "source.baml-jinja" }],
        },
        {
          begin: "(@{1,2}assert)\\(",
          beginCaptures: {
            1: { name: "entity.name.function.attribute.assert" },
            2: { name: "punctuation.definition.template-expression.begin" },
          },
          end: "()\\)",
          endCaptures: {
            1: { name: "punctuation.definition.template-expression.end" },
          },
          contentName: "string.quoted.block.thing",
          patterns: [{ include: "source.baml-jinja" }],
        },
        {
          begin: '(@{1,2}\\w+)\\(#"',
          beginCaptures: {
            1: { name: "entity.name.function.attribute" },
          },
          end: '"#\\)',
          name: "string.quoted.block.baml",
          patterns: [
            { include: "#comment" },
            { include: "#language_block_python" },
            { include: "#language_block_ts" },
            { include: "#key_value" },
            { include: "#block_string_pair" },
            { include: "#string_literal" },
            {
              match: "\\(",
              name: "punctuation.section.parens.open",
            },
            {
              match: "\\)",
              name: "punctuation.section.parens.close",
            },
          ],
        },
        {
          begin: '(@{1,2}\\w+)\\(#"',
          beginCaptures: {
            1: { name: "entity.name.function.attribute" },
          },
          end: '"#\\)',
          name: "string.quoted.block.baml",
          patterns: [
            { include: "#comment" },
            { include: "#language_block_python" },
            { include: "#language_block_ts" },
            { include: "#key_value" },
            { include: "#block_string_pair" },
            { include: "#string_literal" },
            {
              match: "\\(",
              name: "punctuation.section.parens.open",
            },
            {
              match: "\\)",
              name: "punctuation.section.parens.close",
            },
          ],
        },
        {
          begin: "(@{1,2}\\w+)\\(",
          beginCaptures: {
            1: { name: "entity.name.function.attribute" },
          },
          end: "\\)",
          patterns: [
            { include: "#string_unquoted" },
            { include: "#comment" },
            { include: "#language_block_python" },
            { include: "#language_block_ts" },
            { include: "#key_value" },
            { include: "#block_string_pair" },
            {
              include: "#string_literal",
              name: "string.quoted.double",
            },
            {
              match: "\\(",
              name: "punctuation.section.parens.open",
            },
            {
              match: "\\)",
              name: "punctuation.section.parens.close",
            },
          ],
        },
        {
          begin: '(@{1,2}\\w+)\\("',
          beginCaptures: {
            1: { name: "entity.name.function.attribute" },
          },
          end: '"\\)',
          patterns: [
            {
              include: "#string_literal",
              name: "string.quoted.double",
            },
          ],
        },
        {
          begin: "(@{1,2}\\w+)\\(",
          beginCaptures: {
            1: { name: "entity.name.function.attribute" },
          },
          end: "\\)",
          patterns: [
            {
              match: "\\w+",
              name: "string.unquoted",
            },
          ],
        },
        {
          begin: "(@{1,2}\\w+)\\(#",
          beginCaptures: {
            1: { name: "entity.name.function.attribute" },
          },
          end: "#\\)",
          name: "string.quoted.block.baml",
          patterns: [
            {
              name: "constant.character.escape",
              match: "\\\\.",
            },
            {
              name: "meta.embedded.block_attribute",
              begin: "\\(",
              end: "\\)",
            },
            { include: "#comment" },
            { include: "#language_block_python" },
            { include: "#language_block_ts" },
            { include: "#key_value" },
            { include: "#block_string_pair" },
            { include: "#string_literal" },
            {
              match: ".",
              name: "text.plain",
            },
          ],
        },
      ],
    },
    key_value: {
      begin: "\\s*\\{",
      end: "\\s*\\}",
      patterns: [
        { include: "#comment" },
        { include: "#property_assignment_expression" },
      ],
    },
    property_assignment_expression: {
      patterns: [
        { include: "#key_null_pair" },
        { include: "#language_block_python" },
        { include: "#language_block_ts" },

        { include: "#block_string_pair" },

        { include: "#key_value" },
        { include: "#comment" },

        { include: "#key_string_pair" },

        { include: "#key_quoted_string_pair" },
        { include: "#key_number_pair" },
        { include: "#key_boolean_pair" },
        { include: "#key_array_pair" },
        { include: "#key_custom_string_pair" },
        { include: "#nested_key_value" },
      ],
    },
    nested_key_value: {
      begin: '("\\w+"|\\b\\w+\\b)\\s+\\{',
      end: "\\}",
      captures: {
        1: { name: "variable.other.readwrite.nested_key" },
      },
      contentName: "variable.other.readwrite.nested",
      patterns: [
        { include: "#comment" },
        { include: "#key_value" },
        { include: "#key_null_pair" },
        { include: "#key_string_pair" },
        { include: "#language_block_python" },
        { include: "#language_block_ts" },

        { include: "#block_string_pair" },
        { include: "#key_quoted_string_pair" },
        { include: "#key_number_pair" },
        { include: "#key_boolean_pair" },
        { include: "#key_array_pair" },
        { include: "#key_custom_string_pair" },
      ],
    },
    language_block_jinja: {
      begin: '(jinja)(#{1,3}")',
      beginCaptures: {
        1: { name: "comment.line" },
        2: { name: "string.quoted" },
      },
      end: '\\s*("{1,3}#)',
      endCaptures: {
        1: { name: "string.quoted" },
      },
      contentName: "source.baml-jinja.embedded",
      patterns: [
        {
          include: "source.baml-jinja",
        },
      ],
    },
    language_block_python: {
      begin: '(python)(#{1,3}")',
      beginCaptures: {
        1: { name: "comment.line" },
        2: { name: "string.quoted" },
      },
      end: '\\s*("{1,3}#)',
      endCaptures: {
        1: { name: "string.quoted" },
      },
      contentName: "source.python.embedded",
      patterns: [
        {
          include: "source.python",
        },
      ],
    },
    language_block_ts: {
      begin: '(typescript)(#{1,3}")',
      beginCaptures: {
        1: { name: "comment.line" },
        2: { name: "string.quoted" },
      },
      end: '\\s*("{1,3}#)',
      endCaptures: {
        1: { name: "string.quoted" },
      },
      contentName: "source.ts.embedded",
      patterns: [
        {
          include: "source.ts",
        },
      ],
    },
    block_string: {
      begin: '(#("){1,3})',
      beginCaptures: {
        1: { name: "string.quoted.block.baml.startquote" },
      },
      end: '(("){1,3}#)',
      endCaptures: {
        1: { name: "string.quoted.block.baml.endquote" },
      },
      contentName: "string.quoted.block.baml",
      patterns: [{ include: "source.baml-jinja" }],
    },
    block_string_pair: {
      begin: '(\\w+)?\\s+(#("){1,3})',
      beginCaptures: {
        1: { name: "variable.other.readwrite.block_string_pair" },
        2: { name: "string.quoted.block.baml.startquote" },
      },
      end: '(("){1,3}#)',
      endCaptures: {
        1: { name: "string.quoted.block.baml.endquote" },
      },
      contentName: "string.quoted.block.baml.stringpair",
      patterns: [
        {
          include: "#curly_comment",
        },
        {
          name: "entity.name.type.chat",
          match: "\\{#chat\\([^}]*\\)}",
        },
        {
          name: "keyword.special.string.code",
          match: "\\{#[a-zA-Z_][a-zA-Z0-9_.()><]*}",
        },
      ],
    },
    curly_comment: {
      begin: "\\{//",
      beginCaptures: {},
      end: "//}",
      endCaptures: {},
      name: "comment.line.double-slash.baml",
      patterns: [
        {
          include: "#language_block_python",
        },
        {
          include: "#language_block_ts",
        },
      ],
    },
    key_quoted_string_pair: {
      match: '("[^"]+")\\s+("[^"]+")',
      captures: {
        1: { name: "string.quoted.double" },
        2: { name: "string.quoted.double" },
      },
    },
    key_string_pair: {
      begin: '("\\w+"|\\b\\w+\\b)\\s+(")',
      beginCaptures: {
        1: { name: "variable.other.readwrite.key_string_pair" },
        2: { name: "string.quoted.double" },
      },
      end: '"',
      endCaptures: {
        0: { name: "string.quoted.double" },
      },
      patterns: [
        {
          name: "constant.character.escape",
          match: "\\\\.",
        },
        {
          name: "string.quoted.double",
          match: '[^"\\\\]+',
        },
      ],
    },
    key_custom_string_pair: {
      match: '("\\w+"|\\b\\w+\\b)\\s+((?!null)[^\\s\\[\\{]+)',
      captures: {
        1: { name: "variable.other.readwrite.custom_string" },
        2: { name: "string.unquoted" },
      },
    },
    key_number_pair: {
      match: '("\\w+"|\\b\\w+\\b)\\s+(\\b\\d+\\b)',
      captures: {
        1: { name: "variable.other.readwrite.number_pair" },
        2: { name: "constant.numeric" },
      },
    },
    key_boolean_pair: {
      match: '("\\w+"|\\b\\w+\\b)\\s+(\\btrue\\b|\\bfalse\\b)',
      captures: {
        1: { name: "variable.other.readwrite" },
        2: { name: "constant.language.boolean" },
      },
    },
    key_null_pair: {
      match: '("\\w+"|\\b\\w+\\b)\\s+(\\bnull\\b)',
      captures: {
        1: { name: "variable.other.readwrite.null" },
        2: { name: "constant.language.nil.null" },
      },
    },
    key_array_pair: {
      begin: '("\\w+"|\\b\\w+\\b)\\s+\\[',
      end: "\\]",
      captures: {
        1: { name: "variable.other.readwrite" },
      },
      contentName: "variable.other.readwrite.array",
      patterns: [
        { include: "#key_array_pair" },
        { include: "#string_quoted2" },
        { include: "#constant_numeric" },
      ],
    },
    string_quoted2: {
      name: "string.quoted.double",
      begin: '"',
      end: '"',
      patterns: [
        {
          name: "constant.character.escape",
          match: "\\\\.",
        },
      ],
    },
    string_unquoted: {
      match: "\\b[\\w-]+\\b",
      name: "string.unquoted",
    },
    constant_numeric: {
      match: "\\b\\d+\\b",
      name: "constant.numeric",
    },
    type_alias: {
      begin: "(type)\\s+(\\w+)",
      beginCaptures: {
        1: { name: "storage.type.declaration" },
        2: { name: "entity.name.type" },
      },
      patterns: [{ include: "#comment" }],
    },
    invalid_assignment: {
      name: "invalid.illegal",
      match:
        "\\b[a-zA-Z_][a-zA-Z0-9_]*\\s+[a-zA-Z_][a-zA-Z0-9_]*\\s+[a-zA-Z_][a-zA-Z0-9_]*",
    },
    string_literal: {
      match: '"[^"]*"',
      name: "string.quoted.double",
    },
  },
  scopeName: "source.baml",
};

export { bamlTextmate, bamlJinjaTextmate };
