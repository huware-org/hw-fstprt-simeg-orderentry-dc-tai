# Frontend Update: AI Reasoning Changes

## API Response Structure

The response now includes a **new field** `traffic_light_explanation`:

```json
{
  "mago4_flat_table": [...],
  "global_traffic_light": "green",
  "traffic_light_explanation": "✅ Perfetto! Tutti gli articoli sono stati transcodificati con successo...",
  "execution_log": [...],
  "ai_reasoning": {...}
}
```

## New Field: traffic_light_explanation

This field contains an **AI-generated explanation in Italian** that tells the user:
- ✅ **GREEN**: What went well and that it's ready for import
- ⚠️ **YELLOW**: What needs attention (missing customer, price variance, etc.)
- ❌ **RED**: What critical issues were found (failed transcodification, missing data, etc.)

### Example Values

**GREEN:**
```
"✅ Perfetto! Tutti gli articoli sono stati transcodificati con successo. L'ordine è pronto per l'importazione automatica in Mago4."
```

**YELLOW:**
```
"⚠️ Attenzione: il cliente non è presente nell'anagrafica, variazione prezzi fino al 5.2%. Si consiglia una revisione manuale prima dell'importazione."
```

**RED:**
```
"❌ Problemi critici rilevati: 3 articoli non trovati nella tabella di transcodifica. È necessario un intervento manuale per completare l'ordine."
```

## Implementation

Display this explanation near the traffic light indicator:

```python
def display_traffic_light(traffic_light, explanation):
    """Display traffic light with explanation."""
    
    # Color mapping
    colors = {
        "green": "�",
        "yellow": "🟡", 
        "red": "🔴"
    }
    
    icon = colors.get(traffic_light, "⚪")
    
    return f"""
{icon} **{traffic_light.upper()}**

{explanation}
"""
```

### Gradio Example

```python
with gr.Blocks() as demo:
    # ... other components ...
    
    with gr.Row():
        traffic_output = gr.Markdown(label="🚦 Status")
    
    # In your processing function:
    def process_and_display(file):
        # ... API call ...
        
        traffic_light = data.get("global_traffic_light")
        explanation = data.get("traffic_light_explanation")
        
        # Format for display
        traffic_display = f"## 🚦 {traffic_light.upper()}\n\n{explanation}"
        
        return traffic_display, ...
```

## Summary

**New field added**: `traffic_light_explanation` - display it prominently with the traffic light to help users understand what needs attention.

