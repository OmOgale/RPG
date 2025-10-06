# Free-Chat RPG

A console-based persuasion RPG. Players describe a world, negotiate with NPCs through free-form chat, and watch the scenario branch according to their successes, failures, and compromises.

## Quick Start

1. **Python** 3.10 or newer is recommended.
2. Create and activate a virtual environment (optional but encouraged).
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Provide your OpenAI API key either by exporting it or storing it in a `.env` file (loaded automatically):
   ```bash
   # .env
   OPENAI_API_KEY=<key>
   # optional: RPG_MODEL="gpt-4o-mini"
   ```
   ```bash
   # or via shell export
   export OPENAI_API_KEY=<key>
   ```
5. Run the game:
   ```bash
   python -m src.main
   ```

Set `RPG_MODEL` if you want to target a specific OpenAI model (defaults to `gpt-4o-mini`).

During play, each turn surfaces suggested branches—use them as inspiration, but persuasion stays fully free-form.

Type `log` at any persuasion prompt to export the session journal as JSON under the `journals/` folder.

The CLI uses the `rich` library for colorful panels and tables.

To run the automated tests:

```bash
pytest
```

## Example Playthrough (excerpt)

```
╭───────────────────────────────── Opening Scene ──────────────────────────────────╮
│ You find yourself in the vibrant town of Verdant Grove, surrounded by lush       │
│ greenery and the joyful sounds of Pokémon. The sun shines brightly, casting      │
│ dappled shadows on the cobblestone paths. Trainers battle in the fields while    │
│ the Pokémon Center buzzes with activity.                                         │
╰──────────────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────────── Current Dilemma ─────────────────────────────────╮
│ A notorious gang, the Shadow Syndicate, has been stealing Pokémon from trainers. │
│ Townsfolk are terrified, and rumors swirl about a hidden treasure the gang       │
│ wants. They need a brave hero to confront the gang and restore peace.            │
╰──────────────────────────────────────────────────────────────────────────────────╯
                                                                           NPC Roster                                                                            
╭───────────────────┬────────────┬──────────────┬──────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ Name              │ Resistance │ Relationship │ Personality                                                                                                  │
├───────────────────┼────────────┼──────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Mayor Lily        │          1 │            5 │ Cautious and pragmatic, yet passionate about the town's welfare.                                              │
│ Professor Willow  │          0 │            6 │ Brilliant but eccentric; demands solid evidence before acting.                                                 │
│ Benny the Courier │          0 │            8 │ Enthusiastic helper who loves spreading news, though he exaggerates stories.                                   │
╰───────────────────┴────────────┴──────────────┴──────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

Player: “We should fortify town defenses first.”

╭──────────────────────── NPC Response (Professor Willow) ─────────────────────────╮
│ Fortifying defenses is a wise call! I’ll deploy my gadgets to track Team Rocket  │
│ movements while we reinforce the town. That mix of caution and preparation will  │
│ give us the edge.                                                                │
╰──────────────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────────────────────────────────────────────────────────────╮
│ Outcome: Success                                                                 │
│ Professor Willow backs your plan to fortify defenses and gather intel.           │
│ Resistance shift: 0 (now 0) | Relationship shift: +1 (now 7)                     │
╰──────────────────────────────────────────────────────────────────────────────────╯
                                                                 Branches to Explore                                                                  
╭────┬────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│  # │ Title                      │ Description                                                                                                          │
├────┼────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  1 │ Send Scouts                │ Deploy trusted townsfolk to scout Team Rocket’s hideouts for weaknesses.                                            │
│  2 │ Use Inventions             │ Utilize Professor Willow’s gadgets to track their movements discreetly.                                             │
│  3 │ Leverage Benny’s Network   │ Ask Benny to tap his informants and gather street-level intel.                                                       │
╰────┴────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Design Notes

- **MVC separation**: `GameController` (controller) orchestrates the loop, `GameState`/`TurnRecord` (models) capture data, and `CLIView` (view) owns all I/O. `BaseView` keeps the controller decoupled from presentation.
- **View strategy pattern**: The controller works against `BaseView`, allowing a CLI, GUI, or web view to be swapped in without touching business logic.
- **Service isolation**: `GPTClient` encapsulates LLM access, prompt construction, and response validation (via Pydantic), shielding the rest of the code from API specifics.
- **Branch suggestions**: GPT-proposed branches are stored as narrative hints only; persuasion stays free-form for the player.
- **LLM prompts**: Each turn adds compact context (recent turns, summary of older events, NPC streak info). The system prompt pushes for meaningful plot movement and NPC rotation so turns escalate rather than repeat micro-steps.
- **Relationship & resistance normalization**: Outcomes clamp stat deltas (successes can’t raise resistance, etc.) to keep gameplay consistent with narrative tone.
- **Journal export**: A `JournalExporter` service snapshots history to JSON, giving players an optional record of their run.
- **Replayability**: New worlds, NPC personalities, and branching dilemmas regenerate per session; tight prompts encourage varied outcomes.

## Possible Extensions

1. Persistence layer to save and reload adventures.
2. Additional NPC traits that influence resistance changes (e.g., trust, fear, ambition).
3. Richer UI such as a web front-end with conversation logs and visual relationship meters.
