

export interface ParsedQuestion {
    isMCQ: boolean
    questionText: string
    options: string[]
}

/**
 * Parses the raw question text from the backend to determine if it is an MCQ.
 * The backend formats MCQs by appending "Options:\n- A\n- B..."
 * 
 * @param text - The full question text from the database
 * @returns ParsedQuestion object with separation of text and options
 */
export function parseQuestionText(text: string): ParsedQuestion {
    // Check for the "Options:" marker that the backend adds
    const parts = text.split("\n\nOptions:\n")

    if (parts.length < 2) {
        return {
            isMCQ: false,
            questionText: text,
            options: []
        }
    }

    const questionText = parts[0]
    const optionsBlock = parts[1]

    // Parse lines starting with "- "
    const options = optionsBlock
        .split("\n")
        .map(line => line.trim())
        .filter(line => line.startsWith("- "))
        .map(line => line.substring(2)) // Remove "- " prefix

    // If parsing failed to find options, treat as normal text
    if (options.length === 0) {
        return {
            isMCQ: false,
            questionText: text,
            options: []
        }
    }

    return {
        isMCQ: true,
        questionText,
        options
    }
}
