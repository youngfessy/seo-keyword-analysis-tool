# SEO/AEO/GEO Analysis Tool

A comprehensive multi-channel search optimization tool for **synthesis.com/tutor** that uses Google Search Console data to identify opportunities across traditional SEO, Answer Engine Optimization (AEO), and Generative Engine Optimization (GEO).

## 🎯 What It Does

### 🔍 SEO Analysis
- **Analyzes non-brand keywords** ranking in top 100 positions for synthesis.com/tutor
- **Identifies optimization opportunities** based on position, impressions, CTR, and traffic potential
- **Prioritizes keywords** by opportunity score and potential impact
- **Exports detailed analysis** to CSV for further review and action planning

### 🤖 AEO/GEO Analysis
- **Answer Engine Optimization**: Identifies question-based queries for featured snippets and voice search
- **Generative Engine Optimization**: Analyzes content for AI chatbot and generative search optimization
- **SERP Feature Targeting**: Identifies opportunities for FAQ, How-To, and Knowledge Panel optimization
- **Intent Classification**: Categorizes queries by type (Question-Based, Definition, Comparison, How-To, etc.)

## 📊 Key Features

### 🎯 Analysis Engine
- **CTR Optimization**: High-ranking keywords with low click-through rates
- **Top 10 Push**: Keywords ranking 4-10 with good traffic potential  
- **First Page Push**: Keywords ranking 11-20 that could reach page 1
- **Content Optimization**: Keywords ranking 21-50 needing content improvements
- **Long-term Target**: Keywords ranking 51-100 for future optimization

### 📈 Scoring System
- **Position Score** (40%): Closer to top = higher opportunity
- **Volume Score** (30%): More impressions = higher potential
- **CTR Gap Score** (20%): Bigger CTR improvement potential
- **Traffic Potential** (10%): Expected additional clicks

### 🖥️ Interactive Dashboard
- **Smart Filtering**: Filter by priority, opportunity type, position range, score range
- **Advanced Search**: Find keywords by text search
- **Flexible Sorting**: Sort by any column (ascending/descending)
- **Pagination**: View 25, 50, 100, or 200 rows per page
- **Visual Analytics**: Priority breakdowns and opportunity type charts
- **Color Coding**: High (red), Medium (orange), Low (green) priority highlighting
- **Export Capability**: Download filtered results as CSV
- **Real-time Insights**: Top opportunities and traffic potential summaries

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Google Search Console API
1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Search Console API
3. Create OAuth 2.0 credentials (Desktop Application)
4. Add your credentials to `.env`:

```bash
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here
```

### 3. Run Analysis
```bash
python3 keyword_analyzer.py
```

The tool will:
- Authenticate with Google Search Console (browser-based OAuth)
- Fetch 90 days of keyword data
- Filter out brand keywords and low-impact terms
- Analyze opportunities and export results

### 4. Launch Interactive Dashboards

#### Multi-Channel Dashboard (SEO + AEO/GEO)
```bash
./launch_multi_dashboard.sh
# Or directly: streamlit run multi_dashboard.py --server.port 8502
```

#### Full SEO Dashboard (Complete Analysis)
```bash
./launch_dashboard.sh
# Or directly: streamlit run dashboard.py
```

The dashboards provide:
- **🔍 SEO Tab**: Complete keyword opportunity analysis with filtering, sorting, and management
- **🤖 AEO/GEO Tab**: Answer and generative engine optimization analysis
- **Interactive filtering** by priority, opportunity type, position, and score
- **Sortable columns** with pagination (25/50/100/200 rows per page)
- **Visual charts** showing priority and opportunity type breakdowns
- **Keyword search** functionality
- **Export filtered results** to CSV
- **Quick insights** with top opportunities and traffic potential

## 📈 Sample Results

From our latest analysis of **8,084 keywords**:

- **418 High Priority** opportunities
- **5,453 Medium Priority** opportunities  
- **24,184 additional monthly clicks** potential

### Top Non-Brand Opportunities:
1. **ai math help** (Position 6.5) - Top 10 Push opportunity
2. **educational video games** (Position 6.1) - High traffic potential
3. **elementary math tutor** (Position 13.9) - First page opportunity
4. **ai tutor for kids** (Position 4.3) - Strong conversion potential

## 📁 Output

The tool generates a CSV file with columns:
- Keyword
- Current Position  
- Monthly Impressions/Clicks
- Current CTR vs Potential CTR
- Traffic Potential
- Opportunity Score (0-100)
- Opportunity Type
- Priority Level

## ⚙️ Configuration

Edit `config.py` to customize:
- Target domain and brand keywords
- Analysis time period (default: 90 days)
- Position and impression thresholds
- Opportunity scoring criteria

## 🔍 How It Works

1. **Data Collection**: Fetches keyword performance data from Google Search Console
2. **Filtering**: Removes brand keywords, low-volume terms, and positions >100
3. **Opportunity Analysis**: Calculates CTR gaps, traffic potential, and optimization opportunities
4. **Scoring**: Assigns 0-100 opportunity scores based on multiple factors
5. **Export**: Generates actionable CSV report for SEO team

Built specifically for synthesis.com/tutor's multi-channel search optimization strategy, covering traditional SEO, Answer Engine Optimization (AEO), and Generative Engine Optimization (GEO).

## 🤖 AEO/GEO Features

### Answer Engine Optimization (AEO)
- **Question-Based Query Analysis**: Identifies how/what/why/when queries for featured snippets
- **SERP Feature Targeting**: Opportunities for FAQ, How-To, and Knowledge Panel optimization
- **Answer Potential Scoring**: Prioritizes queries by optimization potential
- **Voice Search Optimization**: Targets natural language and conversational queries

### Generative Engine Optimization (GEO)  
- **AI Training Data Analysis**: Identifies content that AI models may reference
- **Entity Recognition**: Tracks brand and topic entity mentions
- **Authority Signal Analysis**: Monitors E-A-T (Expertise, Authoritativeness, Trustworthiness) indicators
- **Context Optimization**: Analyzes comprehensive content for AI understanding

### Multi-Dashboard Access
- **Combined View**: Single dashboard with SEO and AEO/GEO tabs
- **Specialized Analysis**: Dedicated views for each optimization channel
- **Real-time GSC Data**: Fresh data from Google Search Console for all analyses 