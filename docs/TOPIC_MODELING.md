# Hybrid Topic Modeling for Newsletter Categorization

## Overview

The Gmail Newsletter Manager now uses a **hybrid approach** combining machine learning topic modeling with traditional keyword-based categorization.

## How It Works

### 1. Topic Modeling (Primary)
- Uses **Latent Dirichlet Allocation (LDA)** from scikit-learn
- Automatically discovers topics from your newsletter collection
- Learns patterns from sender names, subjects, and email snippets
- Assigns newsletters to discovered topics with confidence scores

### 2. Keyword Matching (Fallback)
- Falls back to manual keyword/domain rules when:
  - No topic model is trained yet
  - Topic model confidence is below 30%
  - Topic model fails for any reason
- Uses categories from `config.yaml`

## Training the Model

Train the topic model on your existing newsletters:

```bash
# Train with default settings (10 topics)
newsletter-manager train-topics

# Specify number of topics
newsletter-manager train-topics --n-topics 12

# Advanced options
newsletter-manager train-topics \
  --n-topics 15 \
  --min-df 2 \
  --max-df 0.7 \
  --max-newsletters 1000
```

### Parameters

- `--n-topics`: Number of topics to discover (default: 10)
  - Fewer topics = broader categories
  - More topics = more specific categories
  - Recommended: 10-15 for most use cases

- `--min-df`: Minimum document frequency (default: 2)
  - Words must appear in at least this many newsletters
  - Higher values = ignore rare words

- `--max-df`: Maximum document frequency (default: 0.7)
  - Ignore words appearing in more than this % of newsletters
  - Filters out very common words

- `--max-newsletters`: Max newsletters to train on (default: 1000)
  - Use more for better accuracy
  - Use fewer for faster training

## Model Storage

The trained model is saved to:
```
~/.gmail-newsletter-manager/topic_model.pkl
```

The model is automatically loaded when you run any command that categorizes newsletters.

## Discovered Topics

When training completes, you'll see the discovered topics with their top words:

```
Discovered Topics:

  Tech (Topic 0):
    software, code, updates, engineer, product, newsletter, programming
  
  News (Topic 1):
    news, daily, weekly, digest, update, briefing, newsletter
  
  Career (Topic 2):
    job, hiring, interview, position, apply, opportunity, career
```

## Auto-Labeling

The system automatically assigns category labels to topics based on word analysis:
- **Tech**: Keywords like "software", "code", "ai", "developer"
- **Business**: Keywords like "startup", "entrepreneur", "marketing"
- **News**: Keywords like "news", "daily", "update", "briefing"
- **Finance**: Keywords like "investment", "stocks", "crypto", "trading"
- **Design**: Keywords like "design", "ui", "ux", "creative"
- **Career**: Keywords like "job", "hiring", "career", "interview"
- **Product**: Keywords like "product", "launch", "feature", "release"

If no category matches, topics use their top 2 words as labels (e.g., "Engineer_Reply").

## Confidence Scores

Each categorization includes a confidence score (0.0 to 1.0):

- **≥ 0.30**: Topic model result is used
- **< 0.30**: Falls back to keyword matching
- Keyword matching returns 0.80 when matched, 0.00 when not

## Retraining

Retrain periodically as your newsletter collection grows:

```bash
# Retrain after discovering new newsletters
newsletter-manager discover --days 30
newsletter-manager train-topics
```

## Benefits

### Topic Modeling Advantages:
- ✅ Learns from actual newsletter content
- ✅ Discovers patterns you didn't explicitly define
- ✅ Adapts to your specific newsletters
- ✅ Handles new sender domains automatically
- ✅ Groups semantically similar newsletters

### Keyword Fallback Advantages:
- ✅ Works immediately without training
- ✅ Provides explicit control over categories
- ✅ Handles edge cases reliably
- ✅ No dependency on training data quality

## Example Usage

```bash
# 1. Import your emails
newsletter-manager import-takeout ~/Downloads/All\ mail.mbox

# 2. Train the topic model
newsletter-manager train-topics --n-topics 12

# 3. List categorized newsletters
newsletter-manager list --sort count

# 4. Organize with labels
newsletter-manager organize
```

## Technical Details

### Model Architecture
- **Vectorizer**: CountVectorizer with 1000 max features, bigrams, English stop words
- **Algorithm**: Latent Dirichlet Allocation (online learning)
- **Features**: Sender name, subject, snippet combined
- **Preprocessing**: Lowercase, URL removal, special char removal

### Dependencies
- `scikit-learn>=1.0.0`: LDA implementation
- `numpy>=1.21.0`: Numerical operations
- `joblib>=1.0.0`: Model serialization

## Troubleshooting

### Model not loading?
```bash
# Check if model file exists
ls -lh ~/.gmail-newsletter-manager/topic_model.pkl

# Retrain if missing
newsletter-manager train-topics
```

### Getting poor categorizations?
1. Ensure you have enough newsletters (50+ recommended)
2. Try adjusting `--n-topics` (10-15 works well)
3. Retrain after discovering more newsletters
4. Update keywords in `~/.gmail-newsletter-manager/config.yaml`

### Want to disable topic modeling?
```bash
# Delete the model file to use only keywords
rm ~/.gmail-newsletter-manager/topic_model.pkl
```
