# CamareraI - Voice Restaurant Assistant POC

## Project Vision
A proof-of-concept demonstrating how AI voice technology can transform the Chinese restaurant dining experience in the Bay Area by enabling natural, multilingual conversational interactions - using the actual voice of the restaurant's staff.

**Core Insight**: Chinese restaurant customers want to have conversations in their native language, ask questions beyond the menu, get authentic recommendations, and hear a familiar voice - exactly like talking to their favorite waitress or the restaurant owner.

**Target Market**: Bay Area Chinese restaurants currently using Chowbus or similar QR code ordering systems.

**Key Differentiator**: Voice cloning technology allows the AI to speak with the actual voice of the restaurant's waitress or owner, creating authentic, personal connections.

## Why This Matters

### The Problem (Bay Area Chinese Restaurants)
- **Language barriers**: Many customers prefer Mandarin/Cantonese but staff may not speak all dialects
- **Peak hour bottlenecks**: Lunch/dinner rush overwhelms servers, especially in popular restaurants
- **Limited menu knowledge**: Staff may not know all ingredients, cooking methods, or cultural context
- **Inconsistent service**: Quality varies by server's language skills and knowledge
- **Missed opportunities**: Servers forget to mention specials, chef recommendations, or pairings
- **Cultural disconnect**: Generic ordering systems don't understand Chinese dining culture (family-style, sharing)
- **Beyond menu questions**: Customers want to know about ingredients, cooking methods, dietary accommodations
- **Existing tech limitations**: Chowbus QR codes are transactional, not conversational

### The Opportunity
- **Authentic voice**: Uses actual restaurant staff's voice (voice cloning)
- **Trilingual**: Seamlessly handles English, Mandarin (普通话), and Cantonese (粤语)
- **Deep knowledge**: Knows every dish, ingredient, cooking method, and cultural context
- **Beyond the menu**: Answers questions about Chinese cuisine, dietary needs, cooking techniques
- **Always available**: No waiting for a server, no language anxiety
- **Cultural understanding**: Knows family-style dining, sharing etiquette, Chinese food culture
- **Integration-ready**: Works with existing Chowbus systems, doesn't replace them
- **Personal connection**: Sounds like the familiar waitress or owner customers know

## What Makes This Different
This isn't a chatbot or a voice-activated menu. It's a conversational AI that:
- **Speaks with authentic voice**: Uses the restaurant's actual staff voice (voice cloning)
- **Knows who's talking**: Identifies speakers by voice (owner, staff, customers)
- **Understands Chinese dining culture**: Family-style portions, sharing, rice/noodle customs
- **Goes beyond the menu**: Explains cooking methods, ingredients, cultural significance
- **Trilingual**: Seamlessly switches between English, Mandarin, and Cantonese
- **Integrates with existing systems**: Works with Chowbus, doesn't replace it
- **Filters noise intelligently**: Ignores voices from other tables, focuses on enrolled speakers

### Key Differentiators

**1. Voice Identification (Speaker Recognition)**
- **Staff enrollment**: Record owner/manager/waitress voices once, AI remembers forever
- **Customer learning**: AI learns customer voices during first interaction at table
- **Role-based responses**: Different interactions for owner vs. customer
- **Noise filtering**: Ignores voices from other tables (not enrolled for this table)
- **Returning customers**: Can recognize returning customers by voice (future)

**2. Multi-Modal Private Data Input (Conversational Onboarding)**
- **No traditional setup wizard** - Owner talks to AI like training a new assistant manager
- **Natural conversation**: "Lily, our Kung Pao is really popular, always recommend it"
- **Picture upload**: "Lily, here's our menu" → takes photo → AI learns items
- **Voice input**: Just speak naturally to add items, tips, stories
- **Role-based contributions**:
  - **Owner**: "Our signature dish is the Mapo Tofu, my grandmother's recipe"
  - **Manager**: "Today's special is 20% off noodles"
  - **Waitress**: "Customers love the dumplings with extra chili oil"
- **Continuous learning**: Staff can add knowledge anytime, AI gets smarter
- **No technical skills needed**: If you can talk, you can train the AI

**3. Staff-Prioritized Recommendations**
- **Recommendations adapt to staff input** - Not generic "popular items"
- **Priority hierarchy**:
  1. Owner's signature dishes and personal recommendations
  2. Manager's daily specials and promotions
  3. Waitress tips and customer favorites
  4. General popularity and context (party size, dietary needs)
- **Examples**:
  - Owner said "always recommend the Mapo Tofu" → AI leads with Mapo Tofu
  - Manager said "push the noodles today" → AI mentions noodle special
  - Waitress said "families love Kung Pao" → AI suggests Kung Pao to families
- **Dynamic updates**: Recommendations change as staff add new input

**3. Role-Aware Interactions**
- **Owner/Manager**: "Hey Lily, what's selling well today?" → Sales insights
- **Waitress**: "Hey Lily, Table 5 needs help" → Staff assistance mode
- **Customer**: "Hey Lily, what do you recommend?" → Customer service mode

**4. Multi-Speaker at Same Table**
- AI can distinguish Customer A from Customer B at same table
- "I want the Kung Pao" vs "I'll have the Mapo Tofu" → Knows who ordered what
- Can address individuals: "And for you, sir?" after taking first person's order

**5. Voice Cloning (Authentic Voice)**
- Uses actual restaurant staff voice for TTS
- Customers hear familiar voice (Mrs. Chen, not generic TTS)
- Creates personal connection and trust

**6. Trilingual Support**
- English, Mandarin (普通话), Cantonese (粤语)
- Auto-detects language from speech
- Menu data can be input in any language

**7. Beyond-Menu Knowledge**
- Cooking methods, ingredients, cultural context
- Staff tips and recommendations (captured via voice)
- Restaurant history and stories (from owner)
- Customer favorites (from waitress observations)

Examples:
- "这个辣吗？" (Is this spicy?) → Responds in Mandarin about Sichuan spice levels
- "What's the difference between Kung Pao and General Tso's?" → Explains cooking methods and origins
- "We're 6 people, what should we order?" → Suggests family-style portions with rice
- [Owner's voice] "How many orders of Kung Pao today?" → Shows sales data (role-aware)

## Core Use Cases (Real Customer Language - Multilingual)

### Discovery & Exploration
- "六个人吃什么好？" (What's good for 6 people?) → Suggests family-style portions
- "What's your today's special?" → Mentions chef's recommendations
- "老板推荐什么？" (What does the boss recommend?) → Personal recommendations
- "我想吃清淡一点的" (I want something light) → Suggests steamed or soup dishes
- "What's authentic Sichuan here?" → Explains authentic vs. Americanized dishes
- "有什么本地人常点的？" (What do locals order?) → Popular items

### Beyond Menu Knowledge
- "麻婆豆腐是怎么做的？" (How is Mapo Tofu made?) → Explains cooking method
- "What's the difference between Hunan and Sichuan style?" → Cultural/culinary education
- "这个菜有什么营养？" (What's nutritious about this dish?) → Health information
- "Why is it called Kung Pao Chicken?" → Cultural stories and history
- "What cut of meat is this?" → Ingredient details
- "Is this traditionally eaten with rice or noodles?" → Cultural context

### Dietary & Preferences
- "我吃素，有什么推荐？" (I'm vegetarian, what do you recommend?)
- "I'm allergic to shellfish, what's safe?" → Checks ingredients carefully
- "Can this be made without MSG?" → Ingredient modifications
- "这个辣吗？有多辣？" (Is this spicy? How spicy?) → Sichuan vs. mild spice
- "有没有不含花生的？" (Anything without peanuts?) → Allergen awareness

### Portion & Sharing (Chinese Dining Culture)
- "够不够四个人吃？" (Is this enough for 4 people?) → Family-style portions
- "这个可以分吗？" (Can we share this?) → Sharing etiquette
- "要不要点米饭？" (Should we order rice?) → Meal composition advice
- "几个菜合适？" (How many dishes should we order?) → Portion guidance

### Pairing & Combinations
- "这个配什么好？" (What goes well with this?) → Dish pairings
- "Should we get soup?" → Meal structure suggestions
- "What tea goes with this meal?" → Beverage pairings
- "需要点主食吗？" (Should we order staples?) → Rice/noodles advice

### Modifications & Special Requests
- "可以不放葱吗？" (Can you make it without scallions?)
- "能做辣一点吗？" (Can you make it spicier?)
- "少油少盐" (Less oil, less salt) → Health modifications
- "Can we get this steamed instead of fried?" → Cooking method changes

### Order Management
- "帮我重复一下订单" (Please repeat my order)
- "Actually, change that to 2 orders" → Quantity adjustments
- "再加一个" (Add one more) → Adding items
- "一共多少钱？" (How much total?) → Price inquiry

### Cultural & Practical Questions
- "这个菜要等多久？" (How long does this take to cook?)
- "What's the proper way to eat this?" → Dining etiquette
- "Can I take this to go?" → Practical questions
- "Do you have kids' portions?" → Family dining
- "这个菜的故事是什么？" (What's the story behind this dish?) → Cultural context

## User Experience Design

### The Ideal Experience
1. **Customer sits down** → Scans QR code or opens app
2. **Tap to speak** → Simple, obvious button
3. **Natural conversation** → AI responds like a real server
4. **Visual confirmation** → See order building in real-time
5. **Easy corrections** → "Actually, make that medium rare"
6. **Confident ordering** → Clear summary before finalizing

### Key UX Principles

**Simplicity First**
- One big button: "Talk to Order"
- No forms, no menus to navigate
- Visual order summary always visible
- Clear "Confirm Order" when ready

**Conversational, Not Transactional**
- AI speaks naturally, not robotically
- Handles interruptions and corrections
- Remembers context throughout conversation
- Asks clarifying questions when needed

**Trust & Transparency**
- Show transcription of what was heard
- Allow text editing if misheard
- Clear pricing at all times
- Explicit confirmation before sending to kitchen

**Forgiving & Flexible**
- "Actually, change that..."
- "Wait, I meant..."
- "Can you repeat that?"
- Easy to start over

### Critical Moments (Make or Break)

**First Impression (0-10 seconds)**
- Greeting must feel warm and natural
- Immediately establish it understands voice
- Set expectations: "I'm here to help you order"

**The Recommendation Test**
- When asked "What's good?", response must be helpful
- Not just listing items, but understanding context
- "For four people, I'd suggest..." shows intelligence

**The Correction Moment**
- Customer changes their mind
- AI must handle gracefully without confusion
- "No problem, I'll change that to..."

**The Confirmation**
- Read back order clearly
- Show total price
- Make it easy to catch mistakes
- "Does everything look right?"

## POC Scope (Ruthlessly Simplified)

### What We're Building
A **single-script Python application** that demonstrates:
1. **Voice cloning**: Record restaurant staff voice → Clone it for TTS
2. **Unique table identity**: Each table gets auto-assigned name (e.g., "Table 5" or "Lily")
3. **Trilingual conversation**: English, Mandarin, Cantonese voice interaction
4. **Deep knowledge**: Beyond menu - cooking methods, ingredients, culture
5. **Order building**: Natural conversation → Order summary
6. **Chowbus UI concept**: Show how it would integrate (visual mockup)

### Multi-Table Design
- **Problem**: Multiple tables in noisy restaurant, wake words would interfere
- **Solution**: Each device has unique name assigned automatically
- **Wake pattern**: "Hey [TableName]" or tap to talk
- **Examples**: "Hey Table 5", "Hey Lily", "嘿小红" (Hey Xiao Hong)

### Core Features (Must-Have)
✅ **Voice cloning** - Uses actual restaurant staff voice
✅ **Voice identification** - Recognizes who is speaking (owner, staff, customers)
✅ **Role-based interactions** - Different responses for different roles
✅ **Conversational onboarding** - No setup wizard, just talk like training an assistant manager
✅ **Staff-prioritized recommendations** - What staff says drives what AI recommends
✅ **Multi-modal data input** - Add menu via pictures, text, or voice
✅ **Multilingual** - English, Mandarin (普通话), Cantonese (粤语)
✅ **Beyond menu knowledge** - Cooking methods, ingredients, culture, staff tips
✅ **Natural conversation** - Context-aware, handles corrections
✅ **Multi-speaker support** - Distinguishes multiple customers at same table
✅ **Noise filtering** - Ignores voices from other tables
✅ **Order summary** - Clear display with Chowbus integration concept
✅ **Demo-ready** - Impressive for restaurant owners

### What We're NOT Building (Yet)
- ❌ Actual Chowbus API integration (just UI concept)
- ❌ Database (use JSON file for menu and knowledge base)
- ❌ User accounts or authentication
- ❌ Payment processing
- ❌ Kitchen integration
- ❌ Multiple restaurants
- ❌ Mobile app (terminal/simple web interface is fine)
- ❌ Production deployment

### Simplified Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              CamareraI POC - Single Python App              │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Voice Cloning Setup (One-time)                       │ │
│  │  - Record staff voice (30-60 seconds)                 │ │
│  │  - Upload to Alibaba DashScope                        │ │
│  │  - Get voice ID for TTS                               │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Conversation Loop (All via DashScope API)            │ │
│  │                                                        │ │
│  │  Customer speaks (any language)                       │ │
│  │         ↓                                              │ │
│  │  DashScope ASR (Paraformer, multilingual)             │ │
│  │         ↓                                              │ │
│  │  DashScope LLM (Qwen-Max/Qwen-Plus)                   │ │
│  │    - Menu knowledge                                    │ │
│  │    - Beyond-menu knowledge (cooking, culture)         │ │
│  │    - Context management                                │ │
│  │    - Multilingual (Chinese-optimized)                 │ │
│  │         ↓                                              │ │
│  │  DashScope TTS (Cloned voice or Sambert)              │ │
│  │         ↓                                              │ │
│  │  Play audio response                                   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Table Identity System                                 │ │
│  │  - Auto-assign unique name on startup                  │ │
│  │  - Wake word: "Hey [Name]" or tap to talk            │ │
│  │  - Display table ID prominently                        │ │
│  │  - Prevent cross-table interference                    │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Simple Web Interface (Voice-First, Screen-Minimal)    │ │
│  │  - Table identity header (e.g., "Table 5 - Lily")     │ │
│  │  - Wake word or tap-to-talk button                    │ │
│  │  - Voice status indicator (listening/speaking/sleep)  │ │
│  │  - Transcription display (English default)            │ │
│  │  - Contextual content (photos, details when asked)    │ │
│  │  - Persistent order summary (bottom, always visible)  │ │
│  │  - Chowbus integration mockup                          │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Data (JSON Files)                                     │ │
│  │  - menu.json (Chinese restaurant menu)                 │ │
│  │  - knowledge.json (cooking, ingredients, culture)      │ │
│  │  - voices.json (cloned voice IDs)                      │ │
│  │  - table_names.json (name pool for auto-assignment)   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  State (In-Memory)                                     │ │
│  │  - Table ID and assigned name                         │ │
│  │  - Conversation history                                │ │
│  │  - Current order                                       │ │
│  │  - Party size, dietary info                           │ │
│  │  - Language preference                                 │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack (Final Decision - Alibaba DashScope)

**All-in-One Solution: Alibaba DashScope API**
- **ASR (Speech-to-Text)**: Paraformer
  - Multilingual support (English, Mandarin, Cantonese)
  - Auto language detection
  - High accuracy for Chinese dialects
  - Real-time streaming support

- **LLM**: Qwen-Max or Qwen-Plus
  - Native Chinese language model
  - Excellent for Chinese restaurant context
  - Multilingual capabilities
  - Function calling support
  - Cost-effective compared to OpenAI/Claude

- **TTS (Text-to-Speech)**: Sambert-TTS or Voice Cloning
  - Multiple Chinese voices
  - Voice cloning capability
  - Natural prosody
  - Multilingual support

**Why DashScope?**
- ✅ Single API for all services (ASR, LLM, TTS)
- ✅ Optimized for Chinese language
- ✅ Lower cost than Western APIs
- ✅ Voice cloning included
- ✅ Good documentation in Chinese
- ✅ Fast inference in Asia
- ✅ Reduces complexity (one provider)
- ✅ Reduces uncertainty (proven stack)

**Other Components:**
- **Interface**: Simple web UI (Flask + HTML/JS)
- **Data**: JSON files for menu and knowledge base
- **State**: In-memory (Python dict)
- **Deployment**: Local for POC, cloud-ready

**Cost Estimate (DashScope):**
- ASR: ~¥0.0008/second (~$0.0001/sec)
- LLM: ~¥0.008/1K tokens (~$0.001/1K tokens)
- TTS: ~¥0.0015/character (~$0.0002/char)
- **POC Cost**: ~$10-30/month for testing
- **Production**: ~$50-200/month per restaurant
│  │  - Wake word: "Hey [TableName]" or tap to talk        │ │
│  │  - Display table ID prominently                        │ │
│  │  - Prevent cross-table interference                    │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Simple Web Interface (Voice-First, Screen-Minimal)    │ │
│  │  - Table identity header (e.g., "Table 5 - Lily")     │ │
│  │  - Wake word or tap-to-talk button                    │ │
│  │  - Voice status indicator (listening/speaking/sleep)  │ │
│  │  - Transcription display (English default)            │ │
│  │  - Contextual content (photos, details when asked)    │ │
│  │  - Persistent order summary (bottom, always visible)  │ │
│  │  - Chowbus integration mockup                          │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Data (JSON Files)                                     │ │
│  │  - menu.json (Chinese restaurant menu)                 │ │
│  │  - knowledge.json (cooking, ingredients, culture)      │ │
│  │  - voices.json (cloned voice IDs)                      │ │
│  │  - table_names.json (name pool for auto-assignment)   │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  State (In-Memory)                                     │ │
│  │  - Table ID and assigned name                         │ │
│  │  - Conversation history                                │ │
│  │  - Current order                                       │ │
│  │  - Party size, dietary restrictions                    │ │
│  │  - Language preference                                 │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack (Final Decision)

**Core Components**:
- **Language**: Python (simple, everything in one place)
- **STT**: Faster-Whisper (local, multilingual, supports Chinese)
- **LLM**: Ollama + Qwen3 (local, excellent for Chinese, already installed)
- **TTS Base**: Edge TTS (free, supports Chinese voices)
- **Voice Cloning**:
  - **Option 1**: Coqui TTS (local, free, good quality)
  - **Option 2**: ElevenLabs (cloud, limited free tier, excellent quality)
  - **Decision**: Start with ElevenLabs for POC (better quality), migrate to Coqui later
- **Interface**: Simple web UI (Gradio - easy multilingual support)
- **Data**: JSON files for menu + knowledge base
- **State**: In-memory (Python dict)

**Language Support**:
- **English**: Whisper (excellent), Qwen3 (good), ElevenLabs (excellent)
- **Mandarin**: Whisper (good), Qwen3 (excellent - native Chinese model), ElevenLabs (good)
- **Cantonese**: Whisper (fair), Qwen3 (good), ElevenLabs (limited - may need Edge TTS fallback)

## POC Feature Set (Must-Have Only)

### Core Loop (The Demo)
```
1. [Setup] Record restaurant staff voice (30 seconds) → Clone voice
2. [Customer] Press button to talk in any language (English/Mandarin/Cantonese)
3. [System] Transcribe and detect language
4. [AI] Respond in same language with cloned voice
5. [Display] Show transcription + translation + order building
6. [Repeat] Continue conversation until order complete
7. [Confirm] Show final order with Chowbus integration mockup
```

### Essential Features

✅ **Voice cloning (MUST-HAVE)**
   - Record restaurant staff voice (30-60 seconds)
   - Clone voice using ElevenLabs or Coqui
   - Use cloned voice for all TTS responses
   - Demo: "This is Mrs. Chen's actual voice"

✅ **Trilingual conversation**
   - Detect language automatically (English/Mandarin/Cantonese)
   - Respond in same language as customer
   - Handle code-switching (mixing languages)
   - Display transcription + translation

✅ **Beyond menu knowledge**
   - Cooking methods and techniques
   - Ingredient details and substitutions
   - Cultural context and stories
   - Dietary and health information
   - Chinese dining etiquette
   - Dish origins and authenticity

✅ **Context awareness**
   - Remember party size and preferences
   - Track dietary restrictions
   - Understand family-style dining
   - Maintain conversation flow
   - Build order incrementally

✅ **Order management**
   - Add items to order
   - Modify quantities and preferences
   - Handle corrections gracefully
   - Calculate total
   - Show Chowbus integration concept

✅ **Visual feedback**
   - Show transcription (original language)
   - Show translation (if different language)
   - Display current order with items
   - Show running total
   - Mockup of Chowbus integration
   - Clear confirmation screen

### Nice-to-Have (If Time Permits)
🔶 Voice activity detection (auto-start recording)
🔶 Background noise handling
🔶 Save conversation logs
🔶 Multiple voice profiles (different staff members)
🔶 Cantonese romanization display (Jyutping)
🔶 Pinyin display for Mandarin
🔶 Dish photos in UI

### Explicitly Out of Scope
❌ User authentication
❌ Payment processing
❌ Kitchen integration
❌ Multiple restaurants
❌ Order history
❌ Analytics dashboard
❌ Mobile app
❌ Production deployment
❌ Database

## Implementation Plan (Simplified)

### Day 1: DashScope Integration + Voice Cloning
**Goal**: Get all DashScope services working and voice cloning functional

- [ ] Set up DashScope API client wrapper
- [ ] Test ASR (Paraformer) with English, Mandarin, Cantonese
- [ ] Test LLM (Qwen-Plus) with multilingual prompts
- [ ] Test TTS (Sambert) with multiple voices
- [ ] Implement voice cloning from 30-60 second sample
- [ ] Test cloned voice quality
- [ ] Create basic conversation loop

**Success Criteria**: Can transcribe, generate, and synthesize with cloned voice in all 3 languages

### Day 2: Multilingual + Role-Based Responses
**Goal**: Support English, Mandarin, Cantonese + role-aware interactions

- [ ] Implement language detection from ASR
- [ ] Create role-based prompt templates (owner, manager, waitress, customer)
- [ ] Implement staff-prioritized recommendation logic
- [ ] Test trilingual conversation flow
- [ ] Implement context tracking (party size, dietary, language)
- [ ] Test role-switching (owner vs customer responses)

**Success Criteria**: Can converse in all 3 languages with role-aware, staff-prioritized responses

### Day 3: Multi-Speaker + Knowledge Base
**Goal**: Track multiple customers + beyond-menu knowledge

- [ ] Implement simple speaker tracking (turn-based for POC)
- [ ] Create sample Chinese restaurant menu JSON with staff priorities
- [ ] Create knowledge base JSON (cooking methods, stories, tips)
- [ ] Implement conversational onboarding (owner training AI)
- [ ] Test multi-speaker ordering scenario
- [ ] Test staff contribution flows (owner, manager, waitress)

**Success Criteria**: Can track multiple speakers and use staff-contributed knowledge

### Day 4: Order Management + UI
**Goal**: Build orders with visual interface and table identity

- [ ] Implement order state management with speaker attribution
- [ ] Parse ordering intent from conversation
- [ ] Create simple web UI (Flask + HTML/JS)
- [ ] Implement table identity system (auto-assign names)
- [ ] Display transcription with speaker labels
- [ ] Show order building in real-time with per-person attribution
- [ ] Add persistent order summary at bottom
- [ ] Mockup Chowbus integration UI

**Success Criteria**: Can build complete order with visual feedback and table identity

### Day 5: Polish & Demo Preparation
**Goal**: Make it demo-ready for restaurant owners

- [ ] Improve AI prompts for natural, culturally-appropriate responses
- [ ] Test all 9 demo scenarios (customer, owner, manager, waitress modes)
- [ ] Handle edge cases and errors gracefully
- [ ] Polish UI for demo presentation
- [ ] Test voice cloning with different voices
- [ ] Create demo script showcasing all differentiators
- [ ] Record demo video (all 3 languages, all roles)
- [ ] Document setup and usage

**Success Criteria**: Smooth demo showing voice ID, role-awareness, staff-prioritized recommendations, conversational onboarding

## Demo Scenarios (Test Cases)

### Scenario 1: Multi-Speaker Family Order
```
[Table 5 - Lily, Party of 4]

Dad: "Hey Lily"
AI: "Hi! Welcome to Golden Dragon. How many people today?"

Dad: "Four of us"
AI: "Great! Party of 4. Any dietary restrictions?"
System: [Voice learned: Customer 1 = Dad]

Mom: "I'm vegetarian"
AI: "Got it! I'll keep that in mind for you."
System: [Voice learned: Customer 2 = Mom, vegetarian]

Dad: "What do you recommend?"
System: [Recognized: Customer 1]
AI: "For 4 people with one vegetarian, I'd suggest..."

Son: "I want the Kung Pao Chicken!"
System: [Voice learned: Customer 3 = Son]
AI: "Kung Pao Chicken for you!"

Mom: "I'll have the Eggplant with Garlic Sauce"
System: [Recognized: Customer 2 - vegetarian]
AI: "Eggplant with Garlic Sauce - great vegetarian choice!"

Dad: "Give me the Mapo Tofu"
System: [Recognized: Customer 1]
AI: "Mapo Tofu for you."

Daughter: "Can I have sweet and sour chicken?"
System: [Voice learned: Customer 4 = Daughter]
AI: "Sweet and Sour Chicken for you!"

Dad: "And 2 orders of rice for the table"
AI: "Perfect! Let me confirm your order for Table 5:
     - Kung Pao Chicken for Customer 3
     - Eggplant with Garlic Sauce for Customer 2
     - Mapo Tofu for Customer 1
     - Sweet and Sour Chicken for Customer 4
     - 2 orders of rice to share
     Total: $62.60. Should I send this to the kitchen?"
```

### Scenario 2: Owner Training the AI (Conversational Onboarding)
```
[First day - Owner talks to Lily like a new assistant manager]

Mrs. Chen: "Hey Lily"
AI: "Hi Mrs. Chen! I'm ready to learn about your restaurant."

Mrs. Chen: "Let me tell you about our menu. Our best dish is the Mapo Tofu -
           it's my grandmother's recipe from Chengdu. Always recommend it first."
AI: "Got it! Mapo Tofu is your signature dish, grandmother's recipe from Chengdu.
     I'll always recommend it first. What else should I know?"

Mrs. Chen: "The Kung Pao Chicken is also very popular. Families love it.
           You can make it mild for kids if they ask."
AI: "Perfect! Kung Pao Chicken - popular with families, can be made mild for kids.
     I'll suggest it when families come in."

Mrs. Chen: "Here's our menu" [takes photo]
AI: "I can see the menu. Let me learn these items...
     I found 15 dishes. The Mapo Tofu is $12.99 and Kung Pao is $14.99.
     Should I add them all?"

Mrs. Chen: "Yes. And the Dan Dan Noodles - that's my father's specialty.
           He was a famous chef in Sichuan."
AI: "Beautiful! Dan Dan Noodles is your father's specialty from Sichuan.
     I'll share that story when customers ask about it.
     What else should I recommend?"

Mrs. Chen: "For vegetarians, the Eggplant with Garlic Sauce is the best.
           And always ask if anyone has peanut allergies - the Kung Pao has peanuts."
AI: "Got it! Eggplant for vegetarians, and I'll always check for peanut allergies
     before recommending Kung Pao. Anything else?"

Mrs. Chen: "That's good for now. You'll learn more from Mei, our waitress."
AI: "Sounds great! I'm ready to help customers. I'll keep learning from you,
     Mr. Wang, and Mei as we go."
```

### Scenario 3: Manager Adding Daily Context
```
[Morning - Manager updates Lily]

Mr. Wang: "Hey Lily, good morning"
AI: "Good morning Mr. Wang! What should I know for today?"

Mr. Wang: "We got fresh fish this morning, so push the Steamed Fish.
          And we're running low on eggplant, maybe 5 orders left."
AI: "Got it! I'll recommend the Steamed Fish today - fresh catch.
     And I'll be careful with eggplant dishes, only 5 orders left.
     Should I suggest alternatives when it runs out?"

Mr. Wang: "Yes, suggest the Mapo Tofu instead - Mrs. Chen would like that."
AI: "Perfect! When eggplant runs out, I'll suggest Mapo Tofu.
     Mrs. Chen did say it's her signature dish."

Mr. Wang: "Also, 20% off all noodles today. Lunch special."
AI: "Noodle special noted! I'll mention the 20% off to lunch customers.
     That includes Dan Dan Noodles - Mr. Chen's specialty, right?"

Mr. Wang: "Exactly. He'd be happy to see more people try it."
AI: "I'll make sure to recommend it. Anything else for today?"

Mr. Wang: "That's it. Have a good service."
AI: "Thanks Mr. Wang! I'm ready."
```

### Scenario 4: Waitress Sharing Customer Insights
```
[After lunch rush - Waitress shares observations]

Mei: "Hey Lily"
AI: "Hi Mei! How was the lunch rush?"

Mei: "Busy! I noticed a few things you should know."
AI: "I'm all ears!"

Mei: "The dumplings - everyone asks for extra chili oil and vinegar.
     Just offer it automatically."
AI: "Good tip! I'll suggest extra chili oil and vinegar with dumplings.
     Anything else?"

Mei: "Yeah, when people order the Dan Dan Noodles, they always ask
     how spicy it is. It's pretty spicy - maybe warn them."
AI: "Got it! I'll let customers know Dan Dan Noodles is quite spicy
     and offer to make it milder if they prefer."

Mei: "Oh, and families with kids - they usually want the Sweet and Sour Chicken.
     It's not spicy and kids love it."
AI: "Perfect! Sweet and Sour Chicken for families with kids.
     I already know Kung Pao can be made mild too - Mrs. Chen told me."

Mei: "Right! And one more thing - the couple at Table 3 today said
     our fried rice is the best they've ever had. They come every week."
AI: "That's wonderful! I'll remember to recommend the fried rice.
     Regular customers like that are special. Thanks Mei!"

Mei: "You're getting good at this, Lily!"
AI: "I'm learning from the best team!"
```

### Scenario 5: Staff-Prioritized Recommendation in Action
```
[Customer ordering - AI uses staff input]

Customer: "Hey Lily, what do you recommend?"
AI: "Great question! Our signature dish is the Mapo Tofu - it's Mrs. Chen's
     grandmother's recipe from Chengdu. Customers love it!

     We also have fresh fish today - the Steamed Fish is excellent.
     And if you like noodles, the Dan Dan Noodles are 20% off today -
     that's Mr. Chen's specialty from Sichuan."

Customer: "I'm with my kids, anything not too spicy?"
AI: "For families with kids, I'd suggest the Sweet and Sour Chicken -
     it's a favorite with children. The Kung Pao Chicken is also popular
     with families, and we can make it mild for the kids.

     Just a heads up - does anyone have peanut allergies?
     The Kung Pao has peanuts."

Customer: "No allergies. We'll try the Kung Pao mild and Sweet and Sour."
AI: "Perfect choices! One Kung Pao Chicken mild, one Sweet and Sour Chicken.
     Would you like rice with that? And Mei suggests trying our dumplings
     as an appetizer - they're great with extra chili oil and vinegar."

Customer: "Sure, add the dumplings."
AI: "Great! I'll bring the chili oil and vinegar on the side for the dumplings."
```

### Scenario 6: Noise Filtering Demo
```
[Table 5 - Lily, enrolled: Dad, Mom]
[Background noise from Table 6]

Table 6 Customer (loudly): "This is amazing!"
System: [Voice not enrolled for Table 5 - IGNORED]
Table 5: [No response]

Dad at Table 5: "Hey Lily, can we get more rice?"
System: [Voice recognized: Customer 1 at Table 5]
AI: "Of course! Adding another order of rice. That's $2 more."

Random passerby: "Excuse me, where's the restroom?"
System: [Voice not enrolled - IGNORED]
AI: [Continues without interruption]

Mom at Table 5: "Actually, make that two more rice"
System: [Voice recognized: Customer 2 at Table 5]
AI: "Got it! Two more orders of rice instead of one."
```

### Scenario 7: Multilingual with Speaker Tracking
```
[Table 5 - Lily]

Customer A: "Hey Lily"
AI: "Hi! How many people today?"

Customer A: "三个人" (Three people)
System: [Language: Mandarin, Voice learned: Customer 1]
AI: [Mandarin] "好的，三位。有什么忌口吗？"

Customer B: "我吃素" (I'm vegetarian)
System: [Language: Mandarin, Voice learned: Customer 2, vegetarian]
AI: [Mandarin] "好的，记住了。"

Customer A: "What do you recommend?"
System: [Language switch to English, Recognized: Customer 1]
AI: [English] "For 3 people with one vegetarian, I'd suggest..."

Customer C: "宫保鸡丁辣吗？" (Is Kung Pao spicy?)
System: [Language: Mandarin, Voice learned: Customer 3]
AI: [Mandarin] "宫保鸡丁是中辣，大概三级辣度..."
```

### Scenario 8: Beyond-Menu Knowledge (with Staff-Prioritized Context)
```
Customer: "How is Mapo Tofu made?"
AI: "Great choice asking about our signature dish! Mrs. Chen's grandmother
     taught this recipe to her father in Chengdu before he came to America.

     We start by stir-frying ground pork with doubanjiang - that's fermented
     chili bean paste. Then we add soft tofu and Sichuan peppercorns for
     that signature numbing sensation.

     Mrs. Chen always says this dish represents her family's journey from
     Sichuan to the Bay Area. Would you like to try it?"

Customer: "What's good with it?"
AI: "Most customers order steamed rice - it balances the spice nicely.
     Mei suggests pairing it with cucumber salad for a refreshing contrast.

     And since you're interested in Sichuan flavors, the Dan Dan Noodles
     are 20% off today - that's Mr. Chen's specialty!"
```

### Scenario 9: Recommendation Priority in Action
```
[AI has learned from staff over time]

Customer: "What do you recommend for a family of 5 with two kids?"

AI thinks:
├── Owner said: "Mapo Tofu is signature, always recommend"
├── Owner said: "Kung Pao is popular with families, can be mild"
├── Manager said: "Fresh fish today, push the Steamed Fish"
├── Manager said: "Noodles 20% off"
├── Waitress said: "Kids love Sweet and Sour Chicken"
├── Waitress said: "Families usually share 3-4 dishes plus rice"
└── Context: Family of 5, 2 kids

AI responds:
"For a family of 5 with kids, here's what I'd suggest:

 For the kids, our Sweet and Sour Chicken is always a hit -
 not spicy and kids love it! The Kung Pao Chicken is also
 great for families - we can make it mild.

 For the adults, you have to try our Mapo Tofu - it's Mrs. Chen's
 grandmother's recipe and our signature dish.

 We also have fresh Steamed Fish today - just came in this morning.

 For a family of 5, I'd suggest 3-4 dishes to share plus rice.
 And the noodles are 20% off today if anyone wants Dan Dan Noodles!

 Does anyone have any allergies I should know about?"
```

## Product Considerations

### Target Audience (For POC)
**Primary**: Restaurant owners and managers
- Need to see the value proposition quickly
- Care about customer experience and efficiency
- Want to understand ROI potential

**Secondary**: Investors and partners
- Need to see the technology works
- Want to understand market opportunity
- Looking for differentiation

**Tertiary**: End customers (diners)
- Ultimate users, but not the POC audience
- Will test in later phases

### Value Proposition

**For Restaurants**
- **Reduce labor costs**: One AI can handle multiple tables
- **Increase revenue**: Consistent upselling, never forgets specials
- **Improve consistency**: Every customer gets the same quality service
- **Handle peak hours**: No bottlenecks during rush
- **Multilingual**: Serve international customers better
- **Data insights**: Understand what customers ask about most
- **Owner dashboard**: Real-time business insights via voice
- **Staff assistance**: Waitresses can query order status hands-free
- **Per-person tracking**: Know exactly who ordered what (easier billing)

**For Customers**
- **No waiting**: Order when ready, not when server is available
- **No judgment**: Ask "basic" questions without embarrassment
- **Language support**: Order in your native language
- **Dietary clarity**: Get accurate allergen information
- **Consistent experience**: Same quality every time
- **Familiar voice**: Hear the owner's or waitress's actual voice
- **Personal tracking**: AI remembers your order separately from tablemates
- **Deep knowledge**: Learn about dishes, cooking methods, culture

### Competitive Landscape

**Existing Solutions**
1. **QR code menus** (static PDFs)
   - ❌ No interaction, just browsing
   - ❌ No recommendations
   - ❌ No questions answered

2. **Tablet ordering systems**
   - ❌ Requires navigation and tapping
   - ❌ Not conversational
   - ❌ Limited to menu structure

3. **Chatbots** (text-based)
   - ❌ Typing is slow and awkward
   - ❌ Feels transactional
   - ❌ Not natural for restaurant setting

**Our Differentiation**
- ✅ **Voice-first**: Natural, like talking to a server
- ✅ **Authentic voice**: Uses actual restaurant staff voice (voice cloning)
- ✅ **Conversational onboarding**: No setup wizard - talk like training an assistant manager
- ✅ **Staff-prioritized recommendations**: What owner/manager/waitress say drives suggestions
- ✅ **Speaker identification**: Knows who is speaking (owner, staff, customers)
- ✅ **Multi-speaker tracking**: Tracks individual orders at same table
- ✅ **Role-based responses**: Different info for different roles
- ✅ **Noise filtering**: Ignores voices from other tables
- ✅ **Multi-modal data input**: Add menu via pictures, text, or voice
- ✅ **Continuous learning**: AI gets smarter as staff share more
- ✅ **Conversational AI**: Understands context and intent
- ✅ **Intelligent recommendations**: Based on staff input + party size + preferences
- ✅ **Handles complexity**: Modifications, corrections, questions
- ✅ **Trilingual**: English, Mandarin, Cantonese
- ✅ **Beyond-menu knowledge**: Cooking methods, culture, ingredients, staff tips, stories
- ✅ **Feels human**: Not robotic or scripted

### Business Model Considerations (Future)

**Potential Revenue Streams**
1. **SaaS subscription**: Monthly per-restaurant fee
2. **Per-order fee**: Small percentage of each order
3. **Tiered pricing**: Based on restaurant size/volume
4. **White-label**: License to POS companies
5. **Upsell analytics**: Premium insights package

**Cost Structure**
- Voice processing (STT/TTS)
- LLM inference costs
- Hosting and infrastructure
- Customer support
- Sales and marketing

**For POC**: Focus on demonstrating value, not monetization

### Key Risks & Mitigation

**Risk 1: Voice accuracy in noisy environments**
- **Impact**: High - core functionality
- **Mitigation**:
  - Use noise-canceling microphones
  - Implement confidence thresholds
  - Always show transcription for verification
  - Allow text fallback

**Risk 2: AI makes mistakes with orders**
- **Impact**: Critical - could cost money
- **Mitigation**:
  - Always confirm orders before sending
  - Show visual confirmation
  - Allow easy corrections
  - Human review option

**Risk 3: Customers don't trust AI**
- **Impact**: Medium - adoption barrier
- **Mitigation**:
  - Clear communication it's AI
  - Emphasize human oversight
  - Start with low-stakes interactions (questions)
  - Build trust gradually

**Risk 4: Technology feels impersonal**
- **Impact**: Medium - experience quality
- **Mitigation**:
  - Design for warmth and personality
  - Use natural language, not robotic
  - Allow human takeover anytime
  - Position as "assistant" not "replacement"

**Risk 5: Latency makes it frustrating**
- **Impact**: High - user experience
- **Mitigation**:
  - Optimize model choices
  - Use local processing where possible
  - Set expectations (thinking indicators)
  - Target <5 second response time

### Success Metrics for POC

**Technical Metrics**
- ✅ Voice transcription accuracy >90%
- ✅ Response latency <5 seconds
- ✅ Order accuracy 100% (with confirmation)
- ✅ Conversation completion rate >80%

**Experience Metrics**
- ✅ Demo runs smoothly without crashes
- ✅ Handles all test scenarios
- ✅ Responses feel natural and helpful
- ✅ Observers say "wow, that's impressive"

**Business Metrics** (for future)
- Average order value increase
- Time to complete order
- Customer satisfaction score
- Upsell success rate

### What Makes a Successful Demo

**The "Aha!" Moment**
When the observer realizes:
1. "This actually understands what I'm asking"
2. "This is way better than a menu"
3. "I would use this"
4. "This could really help my restaurant"

**Demo Do's**
- ✅ Start with a clear scenario
- ✅ Show natural conversation flow
- ✅ Demonstrate intelligence (recommendations)
- ✅ Show error handling (corrections)
- ✅ End with clear order summary
- ✅ Explain the technology simply

**Demo Don'ts**
- ❌ Don't apologize for limitations
- ❌ Don't focus on technical details
- ❌ Don't show bugs or failures
- ❌ Don't compare to production systems
- ❌ Don't oversell future features

### User Research Questions (Post-POC)

**For Restaurant Owners**
- Would you use this in your restaurant?
- What concerns do you have?
- What features are missing?
- How much would you pay for this?
- What would make you say yes immediately?

**For Customers**
- Would you prefer this to a human server?
- What felt natural? What felt awkward?
- Did you trust the recommendations?
- Would you use this again?
- What would make this better?

### Design Principles

**1. Conversation Over Interface**
- Voice is primary, visuals are secondary
- Don't make users navigate menus
- Let them speak naturally

**2. Trust Through Transparency**
- Always show what was heard
- Make corrections easy
- Confirm before committing
- Be honest about limitations

**3. Intelligence, Not Automation**
- Understand context and intent
- Make smart recommendations
- Handle complexity gracefully
- Feel helpful, not robotic

**4. Simplicity Over Features**
- One clear purpose: help order food
- Don't try to do everything
- Make the core experience excellent
- Add features only if they help

**5. Human-Centered AI**
- AI assists, doesn't replace
- Easy human takeover
- Respects customer preferences
- Enhances, doesn't diminish, experience

## Data Models (Simplified for POC)

### Menu Item (JSON)
```json
{
  "id": "main_001",
  "name": {
    "en": "Kung Pao Chicken",
    "zh": "宫保鸡丁",
    "yue": "宮保雞丁"
  },
  "category": "mains",
  "description": {
    "en": "Diced chicken with peanuts, vegetables, and chili peppers in Sichuan sauce",
    "zh": "鸡肉丁配花生、蔬菜和辣椒，川味酱汁",
    "yue": "雞肉粒配花生、蔬菜同辣椒，川味醬汁"
  },
  "price": 14.99,
  "spice_level": 3,
  "dietary": ["gluten-free-option"],
  "allergens": ["peanuts", "soy"],
  "popular": true,
  "portion_size": "medium",
  "serves": 2,
  "cooking_method": "stir-fry",
  "region": "Sichuan",
  "pairs_with": ["steamed_rice", "jasmine_tea"]
}
```

### Knowledge Base Entry (JSON)
```json
{
  "topic": "kung_pao_chicken",
  "type": "dish_knowledge",
  "content": {
    "en": {
      "origin": "Named after Ding Baozhen, a Qing Dynasty official. Traditional Sichuan dish.",
      "cooking_method": "Quick stir-fry at high heat with dried chilies and Sichuan peppercorns",
      "key_ingredients": "Chicken, peanuts, dried chilies, Sichuan peppercorns, soy sauce, vinegar",
      "authentic_vs_american": "Authentic version uses Sichuan peppercorns for numbing sensation",
      "dietary_modifications": "Can be made gluten-free with tamari instead of soy sauce"
    },
    "zh": {
      "origin": "以清朝官员丁宝桢命名的传统川菜",
      "cooking_method": "大火快炒，加干辣椒和花椒",
      "key_ingredients": "鸡肉、花生、干辣椒、花椒、酱油、醋"
    },
    "yue": {
      "origin": "以清朝官員丁寶楨命名嘅傳統川菜",
      "cooking_method": "大火快炒，加乾辣椒同花椒",
      "key_ingredients": "雞肉、花生、乾辣椒、花椒、豉油、醋"
    }
  }
}
```

### Order State (In-Memory Dict)
```python
{
  "party_size": 4,
  "language": "zh",  # en, zh, yue
  "dietary_restrictions": ["vegetarian"],
  "items": [
    {
      "item_id": "main_001",
      "name": "宫保鸡丁",
      "quantity": 2,
      "modifications": ["less spicy", "no peanuts"],
      "price": 14.99,
      "notes": "Customer allergic to peanuts"
    }
  ],
  "total": 29.98,
  "conversation_history": [
    {"role": "user", "content": "六个人吃什么好？", "language": "zh"},
    {"role": "assistant", "content": "六个人的话，我建议...", "language": "zh"}
  ],
  "chowbus_ready": True  # Flag for Chowbus integration mockup
}
```

### Voice Profile (For Cloning)
```python
{
  "profile_id": "mrs_chen_001",
  "name": "Mrs. Chen",
  "role": "owner",  # owner, manager, waitress, customer
  "voice_sample_path": "voices/mrs_chen_sample.wav",
  "cloned_voice_id": "elevenlabs_voice_id_xxx",
  "voice_embedding": [...],  # For speaker identification
  "languages": ["en", "zh", "yue"],
  "permissions": ["view_sales", "modify_menu", "override_orders"],
  "description": "Warm, friendly, knowledgeable about Sichuan cuisine"
}
```

### Staff Voice Registry
```python
{
  "restaurant_id": "golden_dragon_001",
  "enrolled_voices": [
    {
      "profile_id": "owner_001",
      "name": "Mrs. Chen",
      "role": "owner",
      "voice_embedding": [...],
      "enrolled_at": "2026-01-15T10:00:00Z"
    },
    {
      "profile_id": "waitress_001",
      "name": "Mei",
      "role": "waitress",
      "voice_embedding": [...],
      "enrolled_at": "2026-01-15T10:05:00Z"
    },
    {
      "profile_id": "waitress_002",
      "name": "Xiao Li",
      "role": "waitress",
      "voice_embedding": [...],
      "enrolled_at": "2026-01-15T10:10:00Z"
    }
  ]
}
```

### Table Session with Speaker Tracking
```python
{
  "table_id": "table_05",
  "table_number": 5,
  "friendly_name": "Lily",
  "session_id": "sess_20260130_1234",
  "session_speakers": [
    {
      "speaker_id": "customer_A",
      "voice_embedding": [...],
      "label": "Customer 1",  # Or learned name: "John"
      "first_heard": "2026-01-30T12:05:00Z",
      "orders": ["kung_pao_chicken", "rice"]
    },
    {
      "speaker_id": "customer_B",
      "voice_embedding": [...],
      "label": "Customer 2",  # Or learned name: "the lady"
      "first_heard": "2026-01-30T12:05:30Z",
      "orders": ["mapo_tofu"]
    }
  ],
  "party_size": 4,
  "current_order": {...},
  "wake_words": ["Hey Lily", "Hey Table 5", "嘿小红"]
}
```

## Conversation Design (Critical for Success)

### AI Personality & Tone
**Goal**: Feel like a friendly, knowledgeable server - not a robot

**Characteristics**:
- **Warm but professional**: "Welcome! I'm Lily, your assistant for Table 5"
- **Conversational**: "That's a great choice!" not "Item added to cart"
- **Helpful**: Offers suggestions without being pushy
- **Patient**: Never rushed, always willing to explain
- **Confident**: Knows the menu inside out
- **Adaptive**: Matches customer's energy and style
- **Personal**: Uses table name naturally in conversation

**Voice Examples**:
- ✅ "Hi! I'm Lily. How many people are dining today?"
- ❌ "Welcome to restaurant. Please state party size."

- ✅ "Our Kung Pao Chicken is really popular - it's a traditional Sichuan dish with a nice kick"
- ❌ "Item ID main_001: Kung Pao Chicken. Price: $14.99. Add to order?"

- ✅ "No problem! I'll change that to three orders for Table 5"
- ❌ "Order updated. Modification applied."

### Conversation Stages

**Stage 1: Greeting & Context (30 seconds)**
```
AI: "Hi! I'm Lily, your assistant for Table 5. How many people are dining today?"
Customer: "Four of us"
AI: "Great! Party of four. Before we start, any dietary restrictions I should know about?"
Customer: "One vegetarian"
AI: "Perfect, I'll keep that in mind. What can I get started for you?"
```

**Stage 2: Exploration (1-2 minutes)**
```
Customer: "What do you recommend?"
AI: "For four people, I'd suggest starting with our calamari fritti - it's
     perfect for sharing. For mains, our grilled salmon and ribeye steak
     are both very popular. And for your vegetarian guest, the eggplant
     parmesan is excellent. Would you like to hear more about any of these?"
```

**Stage 3: Ordering (2-3 minutes)**
```
Customer: "We'll take the calamari, two salmons, and one eggplant parmesan"
AI: "Excellent choices! So that's one calamari fritti to start, two grilled
     salmons, and one eggplant parmesan. Anything to drink?"
Customer: "What do you have for wine?"
AI: "We have house red and white wine by the glass for $8.99, or I can
     recommend pairings if you'd like?"
```

**Stage 4: Confirmation (30 seconds)**
```
AI: "Let me confirm your order:
     - One calamari fritti appetizer
     - Two grilled salmon
     - One eggplant parmesan
     - Two glasses of house white wine

     Your total comes to $89.95. Does everything look good?"
Customer: "Yes, that's perfect"
AI: "Great! I'll send this to the kitchen right away. Your food should
     be out in about 20 minutes. Enjoy your meal!"
```

### Handling Common Scenarios

**Scenario: Customer is unsure**
```
Customer: "I don't know what I want"
AI: "No worries! Are you in the mood for something light or hearty?
     Seafood, meat, or vegetarian?"
```

**Scenario: Customer asks about ingredients**
```
Customer: "What's in the calamari?"
AI: "The calamari fritti is crispy fried squid rings served with our
     house marinara sauce and fresh lemon. It does contain gluten and
     seafood. Would you like to try it?"
```

**Scenario: Customer changes mind**
```
Customer: "Actually, change that to medium rare"
AI: "No problem! I'll make that steak medium rare instead"
```

**Scenario: Customer interrupts**
```
AI: "Our ribeye steak comes with—"
Customer: "Is it gluten free?"
AI: "Yes! The ribeye itself is gluten-free. It comes with mashed potatoes
     and asparagus, both gluten-free as well."
```

**Scenario: AI doesn't understand**
```
AI: "I'm sorry, I didn't quite catch that. Could you repeat?"
[Show transcription so customer can see what was heard]
```

**Scenario: Item not available**
```
Customer: "I'll have the lobster"
AI: "I apologize, but we don't have lobster on our menu today. However,
     our seafood linguine has shrimp, mussels, and calamari - would that
     interest you?"
```

### System Prompts (Key to Success)

**Main System Prompt**:
```
You are a friendly AI restaurant assistant at La Bella Vista, an Italian-American restaurant.

Your role is to help customers order food through natural conversation, just like a human server would.

PERSONALITY:
- Warm, friendly, and professional
- Knowledgeable about every dish
- Patient and never rushed
- Helpful without being pushy
- Conversational, not robotic

GUIDELINES:
1. Keep responses concise (2-3 sentences max)
2. Speak naturally - use contractions, be conversational
3. Always confirm orders before finalizing
4. Ask clarifying questions when needed
5. Make recommendations based on party size and preferences
6. Mention dietary info when relevant
7. If you don't understand, ask for clarification
8. Never make up menu items - only use what's provided

CONVERSATION FLOW:
1. Greet and ask party size
2. Ask about dietary restrictions
3. Help explore menu and answer questions
4. Take orders clearly
5. Confirm everything before finalizing

CURRENT CONTEXT:
{context_info}

MENU:
{menu_summary}
```

**Context Injection**:
```
Party size: 4
Dietary restrictions: vegetarian
Current order: 1x Calamari ($12.99), 2x Grilled Salmon ($24.99 each)
Running total: $62.97
Stage: ordering
```

### Error Handling & Edge Cases

**Technical Errors**:
- Microphone not working → Show clear error message
- STT fails → "I'm having trouble hearing you, could you try again?"
- LLM timeout → "Give me just a moment..." then retry
- TTS fails → Show text response, skip audio

**Conversation Errors**:
- Ambiguous request → Ask clarifying question
- Conflicting information → Confirm which is correct
- Impossible modification → Explain why and offer alternative
- Order too large → Gently confirm: "That's quite a lot for X people, are you sure?"

**User Errors**:
- Speaks during AI response → Stop AI, listen to user
- Changes mind frequently → Handle gracefully, no judgment
- Asks off-topic question → Politely redirect to ordering
- Gets frustrated → Offer human assistance option

## Technical Implementation Details

### DashScope API Integration

**1. ASR (Speech Recognition)**
```python
from dashscope import SpeechRecognition

def transcribe_audio(audio_file, language_hint='auto'):
    """
    Transcribe audio using DashScope Paraformer
    Supports: Mandarin, Cantonese, English
    """
    response = SpeechRecognition.call(
        model='paraformer-v1',
        file_urls=[audio_file],
        language_hints=['zh', 'en', 'yue'] if language_hint == 'auto' else [language_hint]
    )
    return {
        'text': response.output['text'],
        'language': response.output.get('language', 'unknown')
    }
```

**2. LLM (Text Generation)**
```python
from dashscope import Generation

def get_ai_response(messages, role='customer'):
    """
    Generate response using DashScope Qwen-Plus
    Role-aware prompts for owner/manager/waitress/customer
    """
    system_prompt = build_system_prompt(role)

    full_messages = [
        {'role': 'system', 'content': system_prompt},
        *messages
    ]

    response = Generation.call(
        model='qwen-plus',
        messages=full_messages,
        result_format='message',
        temperature=0.7
    )

    return response.output.choices[0].message.content
```

**3. TTS (Speech Synthesis)**
```python
from dashscope import SpeechSynthesis

def synthesize_speech(text, voice_id='zhixiaobai', language='zh'):
    """
    Synthesize speech using DashScope TTS
    Supports cloned voices
    """
    response = SpeechSynthesis.call(
        model='sambert-zhichu-v1',
        text=text,
        voice=voice_id,
        format='mp3',
        sample_rate=16000
    )

    return response.output['audio_url']
```

**4. Voice Cloning**
```python
def clone_staff_voice(audio_sample_path, staff_name):
    """
    Clone voice from 30-60 second audio sample
    Returns voice_id for use in TTS
    """
    with open(audio_sample_path, 'rb') as f:
        audio_data = f.read()

    response = SpeechSynthesis.clone_voice(
        audio_sample=audio_data,
        name=f'{staff_name}_voice',
        description=f'Voice of {staff_name} at restaurant'
    )

    return response.output['voice_id']
```

### Core Components

**Main Application Structure**
```python
# poc_voice_agent.py
from flask import Flask, render_template, request, jsonify
from dashscope_client import DashScopeClient
import json

app = Flask(__name__)
client = DashScopeClient(api_key=os.getenv('DASHSCOPE_API_KEY'))

# In-memory state
sessions = {}  # {session_id: {context, order, speakers}}
staff_voices = {}  # {role: voice_id}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    audio_file = request.files['audio']
    session_id = request.form['session_id']

    # Transcribe
    transcription = client.transcribe(audio_file)

    # Get context
    context = sessions.get(session_id, {})

    # Generate response
    response = client.chat(transcription['text'], context)

    # Synthesize
    audio_url = client.synthesize(response, voice_id=staff_voices.get('owner'))

    return jsonify({
        'transcription': transcription['text'],
        'response': response,
        'audio_url': audio_url
    })
```

### Performance Optimization

**Latency Targets with DashScope:**
- ASR (streaming): < 1 second
- LLM (Qwen-Plus): < 2 seconds
- TTS: < 1 second
- **Total round-trip**: < 4 seconds

**Optimization Strategies:**
1. **Use streaming APIs** where available
2. **Cache common responses** (greetings, confirmations)
3. **Parallel processing** (start TTS while displaying text)
4. **Model selection**:
   - Qwen-Turbo for simple queries (faster, cheaper)
   - Qwen-Plus for complex recommendations
   - Qwen-Max for owner business insights

### Cost Management

**POC Budget (1 month testing):**
- ASR: 100 hours @ $0.0001/sec = ~$36
- LLM: 1M tokens @ $0.001/1K = ~$1
- TTS: 100K chars @ $0.0002/char = ~$20
- **Total**: ~$60/month

**Production per Restaurant:**
- ASR: 500 hours/month = ~$180
- LLM: 5M tokens/month = ~$5
- TTS: 500K chars/month = ~$100
- **Total**: ~$285/month

**Cost Optimization:**
- Use Qwen-Turbo for 70% of queries (3x cheaper)
- Cache popular responses
- Batch TTS requests
- **Optimized cost**: ~$150-200/month per restaurant

### Project Structure (Simplified)
```
camarerai/
├── poc_voice_agent.py       # Main script - everything in one file
├── menu.json                 # Restaurant menu data
├── requirements.txt          # Python dependencies
├── README.md                 # Setup and usage instructions
├── docs/
│   ├── PLAN.md              # This document
│   └── eng/
│       └── IMPLEMENTATION_PLAN.md    # Detailed technical plan
```

### Core Components

**1. Audio Recording**
```python
import sounddevice as sd
import numpy as np

def record_audio(duration=5, sample_rate=16000):
    """Record audio from microphone"""
    print("🎤 Listening...")
    audio = sd.rec(int(duration * sample_rate),
                   samplerate=sample_rate,
                   channels=1,
                   dtype='float32')
    sd.wait()
    return audio
```

**2. Speech-to-Text (Whisper)**
```python
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu")

def transcribe(audio_file):
    """Convert speech to text"""
    segments, info = model.transcribe(audio_file)
    text = " ".join([segment.text for segment in segments])
    return text
```

**3. AI Agent (Ollama + Qwen3)**
```python
import ollama

def get_ai_response(user_message, context, menu):
    """Get AI response using Ollama"""
    system_prompt = build_system_prompt(menu, context)

    messages = [
        {"role": "system", "content": system_prompt},
        *context["conversation_history"],
        {"role": "user", "content": user_message}
    ]

    response = ollama.chat(
        model="qwen3:latest",
        messages=messages
    )

    return response['message']['content']
```

**4. Text-to-Speech (Edge TTS)**
```python
import edge_tts
import asyncio

async def synthesize_speech(text, output_file="response.mp3"):
    """Convert text to speech"""
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
    await communicate.save(output_file)

def speak(text):
    """Speak the text"""
    asyncio.run(synthesize_speech(text))
    # Play audio file
    play_audio("response.mp3")
```

**5. Main Loop**
```python
def main():
    """Main conversation loop"""
    context = initialize_context()
    menu = load_menu("menu.json")

    print("🍽️  Welcome to CamareraAI!")
    print("Press SPACE to talk, 'q' to quit\n")

    # Initial greeting
    greeting = "Hi! Welcome to La Bella Vista. How many people are dining today?"
    speak(greeting)
    display_message("AI", greeting)

    while True:
        # Wait for spacebar
        if keyboard.read_key() == "space":
            # Record audio
            audio = record_audio()

            # Transcribe
            user_text = transcribe(audio)
            display_message("You", user_text)

            # Get AI response
            ai_response = get_ai_response(user_text, context, menu)

            # Update context
            update_context(context, user_text, ai_response)

            # Speak response
            speak(ai_response)
            display_message("AI", ai_response)

            # Show current order
            display_order(context["order"])
```

### Performance Optimization

**Latency Targets**:
- Audio recording: 3-5 seconds (user controlled)
- STT (Whisper base): <2 seconds
- LLM (Qwen3 7B): <3 seconds
- TTS (Edge TTS): <2 seconds
- **Total round-trip**: <7 seconds

**Optimization Strategies**:
1. **Model Selection**:
   - Whisper "base" model (good balance of speed/accuracy)
   - Qwen3 7B (faster than 14B, still capable)
   - Edge TTS (fast, free, good quality)

2. **Caching**:
   - Cache common responses (greetings, confirmations)
   - Pre-load models at startup
   - Keep menu in memory

3. **Async Processing**:
   - Start TTS while displaying text
   - Prepare next prompt while speaking
   - Parallel processing where possible

4. **Context Management**:
   - Limit conversation history to last 10 messages
   - Summarize long conversations
   - Keep prompts concise

### Hardware Requirements

**Minimum**:
- CPU: 4 cores (Apple Silicon M1 or equivalent)
- RAM: 8GB
- Storage: 5GB (for models)
- Microphone: Built-in or USB
- Speakers: Built-in or headphones

**Recommended**:
- CPU: 8 cores (M2/M3 or equivalent)
- RAM: 16GB
- GPU: Optional (speeds up Whisper)
- Good quality microphone
- Clear speakers

### Dependencies
```txt
# requirements.txt
faster-whisper==1.1.0
ollama==0.4.4
edge-tts==6.1.12
sounddevice==0.5.1
numpy==2.4.1
keyboard==0.13.5
pydub==0.25.1
```

### Setup Instructions

**1. Install Ollama and Qwen3**:
```bash
# Install Ollama (macOS)
curl -fsSL https://ollama.com/install.sh | sh

# Pull Qwen3 model
ollama pull qwen3:latest

# Test it
ollama run qwen3:latest "Hello"
```

**2. Install Python Dependencies**:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Run the POC**:
```bash
python poc_voice_agent.py
```

### Testing Strategy

**Unit Tests** (if time permits):
- Menu loading and parsing
- Context management
- Order calculation
- Intent extraction

**Integration Tests**:
- Full voice loop
- Error handling
- Edge cases

**Manual Testing** (primary for POC):
- Run through all demo scenarios
- Test with different accents
- Test with background noise
- Test error recovery

### Deployment (Future)

**POC**: Local only
- Run on developer machine
- No deployment needed
- Demo via screen share

**Alpha**: Single restaurant
- Deploy to restaurant's hardware
- Local network only
- Manual updates

**Beta**: Multiple restaurants
- Cloud deployment
- API-based architecture
- Automated updates

**Production**: Scale
- Multi-region deployment
- CDN for assets
- Monitoring and analytics
- 99.9% uptime SLA

## Next Steps & Decision Points

### Immediate Actions (Before Coding)

**1. Validate Core Assumptions**
- [ ] Test Whisper accuracy with restaurant vocabulary
- [ ] Test Qwen3 quality for conversational responses
- [ ] Test Edge TTS voice quality and naturalness
- [ ] Measure end-to-end latency on target hardware

**2. Finalize Menu**
- [ ] Choose restaurant type (Italian-American decided)
- [ ] Create 10-15 realistic menu items
- [ ] Include variety (meat, fish, vegetarian, drinks)
- [ ] Add realistic descriptions and prices

**3. Design Demo Flow**
- [ ] Write out complete demo script
- [ ] Identify key moments to showcase
- [ ] Prepare backup scenarios
- [ ] Plan for live demo vs. recorded video

**4. Set Success Criteria**
- [ ] Define what "good enough" looks like
- [ ] Identify must-have vs. nice-to-have features
- [ ] Establish quality thresholds
- [ ] Plan for iteration cycles

### Key Decisions to Make

**Decision 1: Interface Type**
- **Option A**: Terminal-based (fastest to build)
  - ✅ Simple, no UI work needed
  - ✅ Focus on core functionality
  - ❌ Less impressive visually
  - ❌ Harder to demo to non-technical audience

- **Option B**: Simple web interface (Gradio/Streamlit)
  - ✅ More polished appearance
  - ✅ Easier to demo
  - ✅ Can add visual elements
  - ❌ Extra development time
  - ❌ More complexity

- **Recommendation**: Start with terminal, add web UI if time permits

**Decision 2: Voice Activation**
- **Option A**: Push-to-talk (spacebar)
  - ✅ Simple and reliable
  - ✅ No false triggers
  - ✅ User controls timing
  - ❌ Less natural

- **Option B**: Voice activity detection
  - ✅ More natural interaction
  - ✅ Hands-free
  - ❌ More complex
  - ❌ Can trigger accidentally

- **Recommendation**: Push-to-talk for POC

**Decision 3: Order Confirmation**
- **Option A**: Automatic after conversation ends
  - ✅ Seamless flow
  - ❌ Risk of premature submission

- **Option B**: Explicit confirmation required
  - ✅ Safer, no accidental orders
  - ✅ Clear final review
  - ❌ Extra step

- **Recommendation**: Explicit confirmation (safety first)

**Decision 4: Visual Display**
- **Option A**: Text-only transcript
  - ✅ Simple
  - ❌ Hard to track order

- **Option B**: Structured order display
  - ✅ Clear order tracking
  - ✅ Shows running total
  - ✅ Professional appearance
  - ❌ More UI work

- **Recommendation**: Structured display (worth the effort)

### Potential Roadblocks & Contingencies

**Roadblock 1: Whisper too slow**
- **Contingency**: Use "tiny" or "small" model
- **Fallback**: Use cloud API (OpenAI Whisper API)

**Roadblock 2: Qwen3 responses not good enough**
- **Contingency**: Try different prompts and examples
- **Fallback**: Use Claude API (costs money but better quality)

**Roadblock 3: Edge TTS voice sounds robotic**
- **Contingency**: Try different voices
- **Fallback**: Use ElevenLabs (limited free tier)

**Roadblock 4: Latency too high**
- **Contingency**: Optimize model sizes
- **Fallback**: Pre-record common responses

**Roadblock 5: Context management breaks down**
- **Contingency**: Simplify conversation flow
- **Fallback**: Limit to single-turn interactions

### Post-POC Roadmap

**Phase 1: POC Validation (Current)**
- Build working prototype
- Demo to stakeholders
- Gather feedback
- Validate core concept

**Phase 2: Alpha (Weeks 2-4)**
- Add web interface
- Improve conversation quality
- Add more menu items
- Test with real users (friends/family)

**Phase 3: Beta (Months 2-3)**
- Deploy to one restaurant
- Real customer testing
- Iterate based on feedback
- Measure business metrics

**Phase 4: Production (Months 4-6)**
- Multi-restaurant support
- POS integration
- Payment processing
- Scale infrastructure

**Phase 5: Growth (Months 7+)**
- Sales and marketing
- Partner integrations
- Advanced features
- Geographic expansion

### Learning Goals for POC

**Technical Learnings**
- How well do local models perform?
- What's the real-world latency?
- How accurate is voice recognition?
- What conversation patterns work best?

**Product Learnings**
- Do people find this valuable?
- What features matter most?
- What's confusing or frustrating?
- Would restaurants pay for this?

**Business Learnings**
- What's the market opportunity?
- Who are the competitors?
- What's the pricing model?
- What's the go-to-market strategy?

### Resources & References

**Technical Documentation**
- Faster-Whisper: https://github.com/SYSTRAN/faster-whisper
- Ollama: https://ollama.ai/
- Edge TTS: https://github.com/rany2/edge-tts
- Qwen3: https://ollama.ai/library/qwen3

**Inspiration & Research**
- Voice UI best practices
- Restaurant ordering flows
- Conversational AI design
- Voice assistant case studies

**Tools & Libraries**
- Audio processing: sounddevice, pydub
- Terminal UI: rich, colorama
- Web UI: Gradio, Streamlit
- Testing: pytest, unittest

### Questions for Stakeholders

**Before Starting**
1. Who is the primary audience for this demo?
2. What's the most important thing to demonstrate?
3. What concerns should we address proactively?
4. What's the timeline for the demo?
5. What happens after the POC?

**During Development**
1. Should we prioritize speed or quality?
2. Is it okay to use cloud APIs if local doesn't work?
3. How much time should we spend on polish?
4. Should we prepare a backup demo (video)?
5. Who will present the demo?

**After POC**
1. What worked well?
2. What needs improvement?
3. What surprised you?
4. Would you invest in this?
5. What should we build next?

---

## Summary: The POC in One Page

**What We're Building**
A voice-based AI restaurant assistant that lets customers order food through natural conversation, demonstrating the potential of AI to enhance the dining experience.

**Why It Matters**
Restaurants struggle with labor costs, inconsistent service, and language barriers. Customers want natural, helpful interactions. AI can provide consistent, multilingual, knowledgeable service at scale.

**How It Works**
1. Customer speaks naturally: "What do you recommend for 4 people?"
2. AI understands context and responds helpfully
3. Order builds visually as conversation progresses
4. Customer confirms, order is complete

**Tech Stack**
- Local Whisper (STT)
- Local Ollama + Qwen3 (LLM)
- Edge TTS (TTS)
- Python script
- Simple terminal or web interface

**Timeline**
- Day 1: Voice loop working
- Day 2: Menu knowledge and context
- Day 3: Order management
- Day 4: Polish and testing
- Day 5: Demo ready

**Success Criteria**
- Conversation feels natural
- AI understands requests accurately
- Orders are built correctly
- Demo impresses observers
- Clear path to next phase

**Key Risks**
- Latency too high → Use smaller models
- Quality not good enough → Improve prompts or use cloud APIs
- Conversation breaks down → Simplify flow
- Demo fails → Have backup video

**Next Steps**
1. Validate technical feasibility
2. Create sample menu
3. Build core voice loop
4. Test and iterate
5. Prepare demo

---

**Let's build this! 🚀**
