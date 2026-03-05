# Gradio Frontend: AI Reasoning Implementation

## API Response Change

The `/api/v1/process-order` endpoint now returns an **optional** `ai_reasoning` field:

```json
{
  "mago4_flat_table": [...],
  "global_traffic_light": "yellow",
  "execution_log": [...],
  "ai_reasoning": {
    "client_type": "lube",
    "strategy": "Lube",
    "reasoning_text": "Ho identificato il documento come un ordine Lube...",
    "extraction_method": "AI with thinking mode"
  }
}
```

**Note**: `ai_reasoning` can be `null` - handle this case!

## Key Points

1. **New field**: `ai_reasoning` is optional (can be `null`)
2. **Display**: Use `gr.Accordion` to keep UI clean
3. **Language**: Reasoning text is in Italian
4. **Purpose**: Show clients how AI interpreted their document

That's it! Just add the accordion component and handle the new field.
