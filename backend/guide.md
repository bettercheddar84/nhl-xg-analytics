LLM-Powered xG Model Architecture for Pittsburgh Penguins
🧠 Hybrid Architecture Overview
Core Concept
Combine a traditional neural xG predictor with an LLM that can:

Explain predictions in natural language
Answer questions about plays and patterns
Generate insights from the data
Provide coaching recommendations

🏗️ Architecture Components
1. Quantitative xG Neural Network
pythonclass XGPredictorNN(nn.Module):
    """Traditional neural network for xG prediction"""
    def __init__(self):
        super().__init__()
        # Your existing 178-feature architecture
        self.spatial_encoder = nn.Linear(5, 32)
        self.temporal_lstm = nn.LSTM(12, 64)
        self.prediction_head = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        # Returns: xG probability + intermediate embeddings
        spatial_emb = self.spatial_encoder(x['spatial'])
        temporal_emb = self.temporal_lstm(x['temporal'])[0]
        
        # Keep embeddings for LLM
        embeddings = torch.cat([spatial_emb, temporal_emb], dim=1)
        xg_prob = self.prediction_head(embeddings)
        
        return xg_prob, embeddings
        
2. Shot Context Encoder
pythonclass ShotContextEncoder:
    """Convert shot data to natural language context"""
    
    def encode_shot(self, shot_data):
        return f"""
        Shot Context:
        - Location: {shot_data['x_coord']}, {shot_data['y_coord']} ({shot_data['danger_level']} danger)
        - Type: {shot_data['shot_type']} from {shot_data['shot_distance']:.1f} feet
        - Angle: {shot_data['shot_angle']:.1f} degrees
        - Game State: {shot_data['strength_state']} ({shot_data['home_score']}-{shot_data['away_score']})
        - Shooter: {shot_data['shooter_name']} vs {shot_data['goalie_name']}
        - Previous Event: {shot_data['prev_event_type']} ({shot_data['time_since_prev_event']:.1f}s ago)
        - Special: {'Rebound' if shot_data['is_rebound'] else ''} {'Rush' if shot_data['is_rush'] else ''}
        """
3. LLM Integration Layer
pythonclass XGExplainerLLM:
    """LLM component for explanations and insights"""
    
    def __init__(self, base_model="llama-3.1-8b"):
        self.llm = AutoModelForCausalLM.from_pretrained(base_model)
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        
        # Fine-tune on hockey analytics data
        self.adapter = LoRAAdapter(
            r=16,
            target_modules=["q_proj", "v_proj"],
            task_type="CAUSAL_LM"
        )
    
    def explain_prediction(self, shot_context, xg_prob, embeddings):
        prompt = f"""
        {shot_context}
        
        Neural Network xG: {xg_prob:.3f}
        
        Explain why this shot has this expected goal probability.
        Consider the key factors that increase or decrease scoring chance.
        """
        
        # Inject embeddings as additional context
        response = self.generate_with_embeddings(prompt, embeddings)
        return response
4. Unified Query Interface
pythonclass PenguinsXGAssistant:
    """Main interface for both predictions and Q&A"""
    
    def __init__(self):
        self.xg_nn = XGPredictorNN()
        self.llm = XGExplainerLLM()
        self.vector_db = ChromaDB()  # For shot similarity search
        
    def process_query(self, query, shot_data=None):
        if shot_data:
            # Prediction + explanation mode
            xg_prob, embeddings = self.xg_nn(shot_data)
            context = ShotContextEncoder.encode_shot(shot_data)
            explanation = self.llm.explain_prediction(context, xg_prob, embeddings)
            
            return {
                "xg_probability": xg_prob,
                "explanation": explanation,
                "similar_shots": self.find_similar_shots(embeddings)
            }
        else:
            # Pure Q&A mode
            return self.answer_analytics_question(query)
    
    def answer_analytics_question(self, query):
        """Answer questions about patterns, players, strategies"""
        # Examples:
        # "What makes Crosby's shots more dangerous than average?"
        # "How do the Penguins perform on rush chances?"
        # "What's our power play shot quality trend?"
        
        relevant_data = self.vector_db.similarity_search(query)
        return self.llm.analyze_pattern(query, relevant_data)
📊 Training Strategy
Phase 1: Train Neural xG Model
python# Traditional supervised learning
optimizer = AdamW(xg_nn.parameters(), lr=0.001)
criterion = FocalLoss(alpha=10.0)  # Handle class imbalance

for epoch in range(100):
    for batch in dataloader:
        xg_pred, _ = xg_nn(batch['features'])
        loss = criterion(xg_pred, batch['is_goal'])
        loss.backward()
        optimizer.step()
Phase 2: Fine-tune LLM on Hockey Analytics
python# Create training data from your shot database
training_examples = []
for shot in shots_with_annotations:
    training_examples.append({
        "context": encode_shot(shot),
        "xg": shot['xg_value'],
        "explanation": shot['expert_annotation']  # If available
    })

# LoRA fine-tuning
peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.1,
)
Phase 3: Create Vector Database
python# Embed all 313k shots for similarity search
shot_embeddings = []
for shot in all_shots:
    _, emb = xg_nn(shot)
    shot_embeddings.append({
        "id": shot['shot_id'],
        "embedding": emb.numpy(),
        "metadata": shot
    })

vector_db.add(shot_embeddings)
🎯 Use Cases
1. Live Game Analysis
python# During Penguins game
shot = get_live_shot_data()
result = assistant.process_query(shot_data=shot)

print(f"xG: {result['xg_probability']:.3f}")
print(f"Analysis: {result['explanation']}")
# "This Malkin one-timer has 0.287 xG due to the royal road pass 
#  and minimal goalie recovery time. Similar to his goal against 
#  Boston on 10/15 (0.291 xG)."
2. Strategic Questions
pythonquery = "How can the Penguins improve their power play shot quality?"
analysis = assistant.process_query(query)

# "Based on 847 Penguins PP shots this season:
#  1. Only 23% come from the slot (league avg: 31%)
#  2. Crosby's PP shots average 0.082 xG vs 0.124 at even strength
#  3. Recommendation: More east-west puck movement to create slot chances..."
3. Player Development
pythonquery = "Which young Penguins players show the best shot selection?"
insights = assistant.process_query(query)

# "Analyzing shot selection metrics for players under 25:
#  - Player X: 0.118 avg xG/shot (78th percentile)
#  - Improves to 0.145 on rush chances
#  - Weakness: Only 0.064 xG on point shots..."
🔧 Implementation Path
Step 1: Data Preparation
python# Create annotated dataset
annotated_shots = []
for shot in significant_shots:  # Goals, near-misses, key saves
    annotated_shots.append({
        "shot_data": shot,
        "annotation": generate_annotation(shot),
        "outcome_context": get_game_impact(shot)
    })
Step 2: Model Training Pipeline
python# train_hybrid_xg_model.py
class HybridXGTrainer:
    def __init__(self):
        self.neural_trainer = NeuralXGTrainer()
        self.llm_trainer = LLMFineTuner()
        
    def train(self, shots_df, annotations_df):
        # Train neural component
        xg_model = self.neural_trainer.train(shots_df)
        
        # Generate embeddings
        embeddings = xg_model.generate_embeddings(shots_df)
        
        # Fine-tune LLM with embeddings
        llm_model = self.llm_trainer.train(
            shots_df, 
            annotations_df, 
            embeddings
        )
        
        return HybridXGModel(xg_model, llm_model)
Step 3: API Development
python# api/xg_assistant.py
@app.post("/analyze_shot")
async def analyze_shot(shot_data: ShotData):
    result = assistant.process_query(shot_data=shot_data.dict())
    return {
        "xg": result["xg_probability"],
        "explanation": result["explanation"],
        "similar_historical": result["similar_shots"][:5]
    }

@app.post("/ask_question")
async def ask_question(query: str):
    return assistant.process_query(query=query)
💡 Advanced Features
1. Multi-Modal Input

Add rink diagrams/video frames
Use vision transformer for spatial understanding

2. Real-Time Learning

Update embeddings with new games
Continuous LLM fine-tuning

3. Coaching Interface
pythonclass CoachingAssistant:
    def generate_scouting_report(self, opponent_team):
        """Generate natural language scouting reports"""
        
    def suggest_lineup_optimization(self, game_situation):
        """Recommend player combinations based on xG patterns"""
        
    def identify_tactical_adjustments(self, period_data):
        """Real-time strategic recommendations"""
🚀 Getting Started

Train base neural xG model (your current path)
Select LLM base model (Llama 3.1 8B recommended for local deployment)
Create annotation dataset (100-1000 expert-annotated shots)
Build vector database (all 313k shots)
Fine-tune LLM (LoRA on hockey analytics)
Deploy API (FastAPI + Redis caching)

This architecture gives you:

Accurate xG predictions (neural network)
Natural language explanations (LLM)
Pattern discovery capabilities
Interactive Q&A about your data
Coaching insights generation
