class ExtractCobolRequirementsRequest {
    cobol_code string
}

class ExtractedRequirementsForExtractCobolRequirements {
    business_logic string[]
    data_structures string[]
    validations string[]
    user_interface_requirements string[]
    integration_points string[]
    summary string
}

function ExtractCobolRequirements(request: ExtractCobolRequirementsRequest) -> ExtractedRequirementsForExtractCobolRequirements {
    client "openai/gpt-4o"
    prompt #"
        You are an expert COBOL analyst. Extract detailed functional requirements from the provided COBOL code.

        <cobol_code>
        {{request.cobol_code}}
        </cobol_code>

        Analyze the COBOL code and extract:

        1. **Business Logic**: Identify all business rules, calculations, and processing logic
        2. **Data Structures**: Document all data definitions, record structures, and file layouts
        3. **Validations**: List all data validation rules and constraints
        4. **User Interface Requirements**: Extract any screen/display requirements or user interactions
        5. **Integration Points**: Identify external system interfaces, file I/O, or database operations

        Provide a comprehensive summary that captures the essence of what this COBOL program does.

        Be thorough and specific in your analysis, as these requirements will be used to create a React application.

        ## Response format
        {{ ctx.output_format}}
    "#
}

test ExtractCobolRequirementsTest {
    functions [ExtractCobolRequirements]
    args {
        request {
            cobol_code #"
            IDENTIFICATION DIVISION.
            PROGRAM-ID. CUSTOMER-REPORT.

            DATA DIVISION.
            FILE SECTION.
            FD CUSTOMER-FILE.
            01 CUSTOMER-RECORD.
                05 CUST-ID PIC 9(5).
                05 CUST-NAME PIC X(30).
                05 CUST-BALANCE PIC 9(7)V99.

            PROCEDURE DIVISION.
            OPEN INPUT CUSTOMER-FILE.
            READ CUSTOMER-FILE AT END MOVE 'Y' TO EOF-FLAG.
            PERFORM UNTIL EOF-FLAG = 'Y'
                IF CUST-BALANCE > 1000
                    DISPLAY CUST-NAME " - High Value Customer"
                END-IF
                READ CUSTOMER-FILE AT END MOVE 'Y' TO EOF-FLAG
            END-PERFORM.
            CLOSE CUSTOMER-FILE.
            STOP RUN.
            "#
        }
    }
}
