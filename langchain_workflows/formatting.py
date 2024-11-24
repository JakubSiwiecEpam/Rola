def _parse_to_markdown_table(data: str):
    try:
        data = eval(data)
        if not data:
            return "Empty data"

        columns = len(max(data, key=len))

        header = "| " + " | ".join(f"Column {i+1}" for i in range(columns)) + " |"
        separator = "|" + "|".join("---" for _ in range(columns)) + "|"

        rows = []
        for item in data:
            row = []
            for i in range(columns):
                if i < len(item):
                    if isinstance(item[i], (list, tuple)):
                        row.append(", ".join(map(str, item[i])))
                    else:
                        row.append(str(item[i]))
                else:
                    row.append("")
            rows.append("| " + " | ".join(row) + " |")

        return "\n".join([header, separator] + rows)
    except:
        return data

def trim_agent_response(text: str) -> str:
    index = text.find("Action: ")
    if index != -1:
        text = text[:index].strip()
    return text

def parse_tool_observetion(tool_name: str, observation: str) -> str:
    match tool_name:
        case "generate_sql_query":
            return observation
        case "execute_sql_query":
            return _parse_to_markdown_table(observation)
        case "_Exception":
            return "I couldn't find any tool I could use to respond to your request"
        case "None":
            return "I am still thinking about what can I do with this question, thank you for your patience!"
    return observation