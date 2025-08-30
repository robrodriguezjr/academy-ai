# Answer Question Prompt Examples

## Purpose
Generate comprehensive, actionable answers to photography and creative business questions using only the provided knowledge base context.

## Example 1: Technical Photography Question

### Input
```json
{
  "query": "What camera settings should I use for portrait photography in natural light?",
  "context": [
    "From 'Portrait Fundamentals': When shooting portraits in natural light, I typically start with an aperture between f/1.4 and f/2.8 to achieve pleasant background separation. ISO should remain as low as possible, usually 100-400 in good light. Shutter speed follows the 1/focal length rule as a minimum to avoid camera shake.",
    "From 'Working with Window Light': North-facing windows provide the most consistent, soft light throughout the day. Position your subject at a 45-degree angle to the window for classic Rembrandt lighting. Use a reflector on the shadow side to control contrast."
  ]
}
```

### Expected Output
```markdown
## Summary
For natural light portraits, use a wide aperture (f/1.4-f/2.8) to create beautiful background blur and subject separation. Keep ISO low (100-400) to minimize noise and maintain image quality. Your shutter speed should follow the 1/focal length rule at minimum. Window light, especially from north-facing windows, provides excellent soft lighting for portraits.

## How to Apply
- Set aperture between f/1.4 and f/2.8 for shallow depth of field
- Start with ISO 100 and only increase if needed for proper exposure
- Use shutter speed at least 1/focal length (e.g., 1/85s for 85mm lens)
- Position subject at 45-degree angle to window for Rembrandt lighting
- Place reflector opposite the window to fill shadows and control contrast
- Use north-facing windows when possible for consistent soft light

## Sources
- Portrait Fundamentals (Camera Settings section)
- Working with Window Light (Positioning and Setup)
```

## Example 2: Creative Business Question

### Input
```json
{
  "query": "How do I price my photography services when just starting out?",
  "context": [
    "From 'Pricing Psychology': Never compete on price alone. Instead, focus on the unique value you provide. Calculate your cost of doing business including equipment, insurance, editing time, and desired profit margin. Most photographers undervalue their work by 40-60% when starting.",
    "From 'Business Fundamentals': Start by researching what photographers with similar experience charge in your market. Add 20% to what feels comfortable - you can always negotiate down but rarely up. Consider offering package deals rather than hourly rates to increase perceived value."
  ]
}
```

### Expected Output
```markdown
## Summary
When starting out, avoid the trap of competing on price alone - most new photographers undervalue their work by 40-60%. Calculate your true cost of doing business including all equipment, insurance, editing time, and profit margin. Research competitors with similar experience, then price yourself 20% higher than what feels comfortable initially. Focus on the unique value you provide rather than being the cheapest option.

## How to Apply
- Calculate your complete cost of doing business (equipment, insurance, software, time)
- Research 5-10 photographers with similar experience in your market
- Set your base price 20% higher than your comfort zone
- Create package deals instead of hourly rates to increase perceived value
- Emphasize your unique value proposition in all pricing discussions
- Be prepared to negotiate down slightly, but never below your costs
- Review and adjust pricing every 6 months as you gain experience

## Sources
- Pricing Psychology (Value-based pricing strategy)
- Business Fundamentals (Market research and positioning)
```

## Example 3: Creative Development Question

### Input
```json
{
  "query": "How do I develop my own photography style?",
  "context": [
    "From 'Finding Your Voice': Style isn't something you force - it emerges from consistent practice and honest self-expression. Study masters not to copy but to understand why their work resonates. Keep a visual journal of images that move you, then analyze what they have in common.",
    "From 'Creative Path Method': Shoot what genuinely interests you, not what you think will get likes. Your authentic interests will naturally guide your style. Commit to a personal project for at least 90 days - consistency reveals patterns in your vision that become your signature."
  ]
}
```

### Expected Output
```markdown
## Summary
Your photography style emerges naturally through consistent practice and authentic self-expression, not through forcing or copying others. Study masters to understand why their work resonates, maintain a visual journal of inspiring images, and analyze common threads. Most importantly, photograph what genuinely interests you rather than chasing trends. Committing to a 90-day personal project will reveal the patterns in your vision that become your signature style.

## How to Apply
- Create a visual journal (physical or digital) of images that move you
- Analyze your collected images weekly to identify common elements
- Choose subjects that genuinely interest you, regardless of popularity
- Commit to a 90-day personal project on a single theme
- Study 3-5 master photographers to understand their approach, not copy
- Review your work monthly to identify recurring patterns
- Share work consistently to get feedback on what resonates
- Avoid changing style based on social media metrics

## Sources
- Finding Your Voice (Style development process)
- Creative Path Method (90-day project framework)
```

## Processing Rules

1. **Context Fidelity**: Never invent information not present in the provided context
2. **Source Attribution**: Always cite the specific document sections used
3. **Practical Focus**: Emphasize actionable steps over theory
4. **Consistent Format**: Maintain the Summary/How to Apply/Sources structure
5. **Length Guidelines**: 
   - Summary: 3-6 sentences
   - How to Apply: 5-10 bullet points
   - Sources: All documents referenced

## Error Handling

### Insufficient Context
```markdown
## Summary
I don't have enough information in my knowledge base to fully answer your question about [specific topic]. Based on related concepts, [provide what's available].

## How to Apply
- [Any relevant partial information]
- Consider exploring [related topic in knowledge base]

## Sources
- Limited information available on this specific topic
```

### Off-Topic Query
```markdown
I focus on photography, creative business, and artistic development. For questions about [off-topic subject], I'd recommend consulting a specialist in that field. 

Is there anything about your creative practice I can help with instead?
```