import streamlit as st
import asyncio
import sys
from pathlib import Path
import os
import shutil
from datetime import datetime
from dotenv import load_dotenv

# Load environment FIRST
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from src.tft_analyzer.models.llm_provider import LLMClient
from src.tft_analyzer.data.riot_api import RiotTFTAPI
from src.tft_analyzer.workflows.comp_analysis_workflow import CompAnalysisWorkflow
from src.tft_analyzer.utils.patch_detector import TFTPatchDetector
from src.tft_analyzer.chat.tft_chat_handler import TFTChatHandler
from src.tft_analyzer.data.patch_data_manager import PatchDataManager


def initialize_settings():
    """Initialize and validate settings"""
    return Settings()




def create_llm_client(settings: Settings) -> LLMClient:
    """Create LLM client with proper API key handling"""
    api_key = settings.get_api_key_for_provider(settings.llm_provider)
    model = settings.get_model_for_provider(settings.llm_provider)
    
    return LLMClient(
        provider=settings.llm_provider,
        model=model,
        api_key=api_key
    )


async def run_analysis_with_progress(settings: Settings, progress_placeholder, status_placeholder):
    """Run the TFT composition analysis with progress updates"""
    try:
        # Step 1: Start parallel initialization (10%)
        progress_placeholder.progress(10)
        status_placeholder.info("🚀 Starting parallel initialization...")
        
        # Create clients immediately (don't wait for patch detection)
        llm_client = create_llm_client(settings)
        use_cache = getattr(settings, 'use_cache', False)
        riot_api = RiotTFTAPI(settings.riot_api_key, settings.riot_region, use_cache=use_cache)
        
        # Step 2: Run patch detection and API testing in parallel (30%)
        progress_placeholder.progress(30)
        status_placeholder.info("🔍 Detecting patch & testing APIs in parallel...")
        
        # Create tasks that can run concurrently
        patch_detector = TFTPatchDetector()
        patch_task = patch_detector.get_current_patch_info()
        api_test_task = riot_api.test_api_connection()
        
        # Wait for both to complete in parallel
        patch_info, api_working = await asyncio.gather(patch_task, api_test_task)
        
        # Update settings with detected patch info
        settings.current_patch = patch_info["patch"]
        settings.current_tft_set = patch_info["set_number"]
        settings.tft_set_name = patch_info["set_name"]
        
        # Step 3: Results of parallel execution (50%)
        progress_placeholder.progress(50)
        if api_working:
            status_placeholder.info("✅ Patch detected & APIs ready!")
        else:
            status_placeholder.warning("⚠️ Patch detected, API connection failed - using mock data")
        
        # Step 4: Start analysis workflow (65%)
        progress_placeholder.progress(65)
        status_placeholder.info("📊 Fetching challenger match data...")
        
        workflow = CompAnalysisWorkflow(llm_client, riot_api, settings)
        
        initial_state = {
            "raw_matches": [],
            "extracted_comps": "",
            "performance_analysis": "",
            "final_report": ""
        }
        
        # Step 5: Run analysis (80%)
        progress_placeholder.progress(80)
        status_placeholder.info("🤖 Analyzing team compositions with AI...")
        
        # Step 6: Performance analysis (90%)
        progress_placeholder.progress(90)
        status_placeholder.info("📈 Evaluating performance patterns...")
        
        final_state = await workflow.graph.ainvoke(initial_state)
        
        # Step 7: Complete (100%)
        progress_placeholder.progress(100)
        status_placeholder.info("✅ Analysis complete!")
        
        # Small delay to show completion
        await asyncio.sleep(0.3)
        
        return final_state["final_report"], patch_info
        
    except Exception as e:
        progress_placeholder.empty()
        status_placeholder.error(f"❌ Analysis failed: {str(e)}")
        return None, None


async def run_analysis(settings: Settings):
    """Run the TFT composition analysis (legacy function for compatibility)"""
    try:
        # Auto-detect current patch
        patch_detector = TFTPatchDetector()
        patch_info = await patch_detector.get_current_patch_info()
        
        # Update settings with patch info
        settings.current_patch = patch_info["patch"]
        settings.current_tft_set = patch_info["set_number"]
        settings.tft_set_name = patch_info["set_name"]
        
        # Initialize clients
        llm_client = create_llm_client(settings)
        use_cache = getattr(settings, 'use_cache', False)
        riot_api = RiotTFTAPI(settings.riot_api_key, settings.riot_region, use_cache=use_cache)
        
        # Test API connection
        api_working = await riot_api.test_api_connection()
        
        if not api_working:
            st.warning("API connection failed - using mock data")
        
        # Create and run analysis workflow
        workflow = CompAnalysisWorkflow(llm_client, riot_api, settings)
        
        initial_state = {
            "raw_matches": [],
            "extracted_comps": "",
            "performance_analysis": "",
            "final_report": ""
        }
        
        final_state = await workflow.graph.ainvoke(initial_state)
        
        return final_state["final_report"], patch_info
        
    except Exception as e:
        st.error(f"Analysis failed: {str(e)}")
        return None, None


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="TFT Comp Analyzer",
        page_icon="⚔️",
        layout="wide"
    )
    
    st.title("⚔️ TFT Set 15: K.O. Coliseum Composition Analyzer")
    st.markdown("*AI-powered analysis of optimal team compositions from challenger gameplay*")
    
    # Navigation tabs
    tab1, tab2 = st.tabs(["📊 Meta Analysis", "💬 TFT Chat"])
    
    # Initialize settings globally
    if 'settings' not in st.session_state:
        st.session_state.settings = initialize_settings()
    
    settings = st.session_state.settings
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Display current configuration with cleaner styling
        with st.container():
            st.markdown("### ⚙️ Current Settings")
            
            # LLM Provider with icon
            provider_icon = "🧠" if settings.llm_provider == "anthropic" else "🤖"
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, #1f1f2e, #2d2d44); padding: 12px; border-radius: 8px; margin: 8px 0;">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 16px; margin-right: 8px;">{provider_icon}</span>
                    <span style="font-weight: bold; color: #FFD700;">LLM Provider</span>
                </div>
                <div style="margin-left: 24px; color: #CCCCCC;">{settings.llm_provider.title()}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Riot Region with icon
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, #1f1f2e, #2d2d44); padding: 12px; border-radius: 8px; margin: 8px 0;">
                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 16px; margin-right: 8px;">🌍</span>
                    <span style="font-weight: bold; color: #FFD700;">Region</span>
                </div>
                <div style="margin-left: 24px; color: #CCCCCC;">{settings.riot_region.upper()}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Patch Selection
        with st.container():
            st.markdown("### 🎯 Patch Selection")
            
            # Initialize patch data manager
            if 'patch_manager' not in st.session_state:
                st.session_state.patch_manager = PatchDataManager()
            
            # Load available patches
            if 'available_patches' not in st.session_state:
                with st.spinner("Loading available patches..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        st.session_state.available_patches = loop.run_until_complete(
                            st.session_state.patch_manager.get_available_patches()
                        )
                    finally:
                        loop.close()
            
            # Patch selection dropdown
            col_patch, col_refresh = st.columns([3, 1])
            
            with col_patch:
                # Set default to current patch from settings or auto-detect
                current_patch = getattr(settings, 'current_patch', '15.17')
                if current_patch not in st.session_state.available_patches:
                    st.session_state.available_patches.insert(0, current_patch)
                
                selected_patch = st.selectbox(
                    "Select Patch Version",
                    st.session_state.available_patches,
                    index=0 if current_patch == st.session_state.available_patches[0] else st.session_state.available_patches.index(current_patch),
                    key="patch_selector"
                )
                
                # Update settings when patch changes
                if selected_patch != getattr(settings, 'current_patch', None):
                    settings.current_patch = selected_patch
                    # Extract set number from patch (assume 15.x = Set 15)
                    major_version = selected_patch.split('.')[0]
                    settings.current_tft_set = int(major_version)
                    
                    # Set appropriate set name
                    if major_version == "15":
                        settings.tft_set_name = "K.O. Coliseum"
                    elif major_version == "14":
                        settings.tft_set_name = "Inkborn Fables"
                    else:
                        settings.tft_set_name = f"Set {major_version}"
            
            with col_refresh:
                st.markdown("<br>", unsafe_allow_html=True)  # Align with selectbox
                if st.button("🔄", help="Refresh patch data"):
                    with st.spinner("Refreshing patch data..."):
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            # Clear cache and reload
                            loop.run_until_complete(
                                st.session_state.patch_manager.clear_cache(selected_patch)
                            )
                            # Reload patch data
                            st.session_state.patch_data = loop.run_until_complete(
                                st.session_state.patch_manager.get_patch_data(selected_patch, force_refresh=True)
                            )
                            st.success("✅ Patch data refreshed!")
                        except Exception as e:
                            st.error(f"Failed to refresh: {str(e)}")
                        finally:
                            loop.close()
            
            # Load patch data for validation
            if 'patch_data' not in st.session_state or st.session_state.get('current_selected_patch') != selected_patch:
                with st.spinner(f"Loading patch {selected_patch} data..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        st.session_state.patch_data = loop.run_until_complete(
                            st.session_state.patch_manager.get_patch_data(selected_patch)
                        )
                        st.session_state.current_selected_patch = selected_patch
                    except Exception as e:
                        st.error(f"Failed to load patch data: {str(e)}")
                        st.session_state.patch_data = None
                    finally:
                        loop.close()
            
            # Display patch info
            if st.session_state.get('patch_data'):
                patch_data = st.session_state.patch_data
                st.markdown(f"""
                <div style="background: linear-gradient(90deg, #1f1f2e, #2d2d44); padding: 12px; border-radius: 8px; margin: 8px 0;">
                    <div style="display: flex; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 16px; margin-right: 8px;">📋</span>
                        <span style="font-weight: bold; color: #FFD700;">Patch Info</span>
                    </div>
                    <div style="margin-left: 24px; color: #CCCCCC;">
                        <div>Set {patch_data.set_number}: {patch_data.set_name}</div>
                        <div style="font-size: 12px; margin-top: 4px;">
                            🏆 {sum(len(champs) for champs in patch_data.champions.values())} Champions<br>
                            ⚡ {len(patch_data.traits)} Traits<br>
                            🎁 {len(patch_data.augments)} Augments<br>
                            ⚔️ {len(patch_data.items)} Items
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning(f"⚠️ Could not load data for patch {selected_patch}")
        
        # API Key status with better styling
        with st.container():
            st.markdown("### 🔑 API Status")
            
            riot_key = settings.riot_api_key
            anthropic_key = settings.anthropic_api_key
            
            riot_present = riot_key and not riot_key.startswith('your_')
            anthropic_present = anthropic_key and anthropic_key.startswith('sk-ant-')
            
            # Riot API status
            riot_color = "#4CAF50" if riot_present else "#F44336"
            riot_icon = "✅" if riot_present else "❌"
            riot_text = "Connected" if riot_present else "Not Connected"
            
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, #1f1f2e, #2d2d44); padding: 12px; border-radius: 8px; margin: 8px 0;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 16px; margin-right: 8px;">🎮</span>
                        <span style="font-weight: bold; color: #FFD700;">Riot Games API</span>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <span style="margin-right: 6px;">{riot_icon}</span>
                        <span style="color: {riot_color}; font-weight: bold;">{riot_text}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Anthropic API status
            anthropic_color = "#4CAF50" if anthropic_present else "#F44336"
            anthropic_icon = "✅" if anthropic_present else "❌"
            anthropic_text = "Connected" if anthropic_present else "Not Connected"
            
            st.markdown(f"""
            <div style="background: linear-gradient(90deg, #1f1f2e, #2d2d44); padding: 12px; border-radius: 8px; margin: 8px 0;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 16px; margin-right: 8px;">🤖</span>
                        <span style="font-weight: bold; color: #FFD700;">Anthropic AI</span>
                    </div>
                    <div style="display: flex; align-items: center;">
                        <span style="margin-right: 6px;">{anthropic_icon}</span>
                        <span style="color: {anthropic_color}; font-weight: bold;">{anthropic_text}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show warning if any API is missing
            if not riot_present or not anthropic_present:
                st.info("💡 Missing API connections will use mock/cached data")
        
        # Development Settings
        with st.container():
            st.markdown("### ⚙️ Development Settings")
            
            # Cache control
            use_cache = st.checkbox(
                "Use Cached Data",
                value=getattr(settings, 'use_cache', False),
                help="Use cached API responses to avoid rate limits during development"
            )
            settings.use_cache = use_cache
            
            # 24-hour filtering
            use_24h_filter = st.checkbox(
                "24-Hour Match Filter",
                value=getattr(settings, 'use_24h_filter', False),
                help="Prefer matches from the last 24 hours (automatically falls back to 7 days, then recent matches if needed)"
            )
            settings.use_24h_filter = use_24h_filter
            
            # Info for 24h filter behavior
            if use_24h_filter:
                st.info("🔄 24-hour filter uses smart fallback: 24h → 7 days → recent matches if needed")
            
            # Display cache status
            if use_cache:
                cache_dir = Path("cache/riot_api")
                if cache_dir.exists():
                    cache_files = list(cache_dir.glob("*.json"))
                    
                    # Analyze cache contents
                    challenger_cache = [f for f in cache_files if "challenger_players" in f.name]
                    match_history_cache = [f for f in cache_files if "match_history" in f.name]
                    match_details_cache = [f for f in cache_files if "match_details" in f.name]
                    
                    # Calculate total cache size
                    total_size = sum(f.stat().st_size for f in cache_files)
                    size_mb = total_size / (1024 * 1024)
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(90deg, #1f1f2e, #2d2d44); padding: 8px; border-radius: 8px; margin: 4px 0;">
                        <div style="display: flex; align-items: center; margin-bottom: 4px;">
                            <span style="font-size: 14px; margin-right: 6px;">💾</span>
                            <span style="color: #CCCCCC; font-size: 14px;">Cache Ready: {len(cache_files)} files ({size_mb:.1f}MB)</span>
                        </div>
                        <div style="margin-left: 20px; color: #AAAAAA; font-size: 12px;">
                            Players: {len(challenger_cache)} • History: {len(match_history_cache)} • Details: {len(match_details_cache)}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Development workflow buttons
                    col_clear, col_info = st.columns([1, 1])
                    
                    with col_clear:
                        if st.button("🗑️ Clear Cache", help="Clear all cached API responses"):
                            if cache_dir.exists():
                                shutil.rmtree(cache_dir)
                                cache_dir.mkdir(parents=True, exist_ok=True)
                            st.success("✅ Cache cleared!")
                            st.rerun()
                    
                    with col_info:
                        if st.button("ℹ️ Cache Info", help="Show cache details"):
                            st.info(f"""
**Cache Durations for Development:**
- Challenger Players: 6 hours
- Match History: 2 hours  
- Match Details: 24 hours

**Quick Iteration Tips:**
- First run: Fetches & caches data
- Subsequent runs: Uses cache instantly
- Cache persists across Streamlit restarts
- Only clear cache when you want fresh data
                            """)
                else:
                    st.info("💡 No cache yet - run analysis once to cache data for fast iteration")
            
            # Show development mode indicator
            if use_cache or use_24h_filter:
                dev_features = []
                if use_cache:
                    dev_features.append("Cached Data")
                if use_24h_filter:
                    dev_features.append("24h Filter")
                
                st.markdown(f"""
                <div style="background: linear-gradient(90deg, #2d4a22, #3e5f2e); padding: 8px; border-radius: 8px; margin: 8px 0;">
                    <div style="display: flex; align-items: center;">
                        <span style="font-size: 14px; margin-right: 6px;">🛠️</span>
                        <span style="color: #90EE90; font-weight: bold; font-size: 14px;">Dev Mode: {' + '.join(dev_features)}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    with tab1:
        # Meta Analysis Tab
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.header("📊 Analysis Request")
            
            st.markdown("""
            Click the button below to analyze current TFT Set 15 meta and get:
            
            - **Top performing compositions**
            - **Meta trends and patterns**  
            - **Strategic recommendations**
            - **Tier rankings**
            
            Analysis uses real challenger gameplay data from recent matches.
            """)
            
            if st.button("🔍 Analyze Current Meta", type="primary", use_container_width=True):
                # Create progress tracking
                progress_placeholder = st.empty()
                status_placeholder = st.empty()
                
                # Run the async analysis with progress updates
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    report, patch_info = loop.run_until_complete(run_analysis_with_progress(settings, progress_placeholder, status_placeholder))
                    
                    if report and patch_info:
                        # Clear progress indicators
                        progress_placeholder.empty()
                        status_placeholder.empty()
                        
                        # Store results in session state with timestamp
                        st.session_state.analysis_report = report
                        st.session_state.patch_info = patch_info
                        st.session_state.analysis_timestamp = datetime.now()
                        st.session_state.analysis_type = "initial"
                        st.success("✅ Analysis complete!")
                        st.rerun()
                finally:
                    loop.close()
        
        with col2:
            st.header("📈 Analysis Results")
            
            # Display results if available
            if hasattr(st.session_state, 'analysis_report') and st.session_state.analysis_report:
                # Display patch info and timestamp
                patch_info = st.session_state.patch_info
                timestamp = getattr(st.session_state, 'analysis_timestamp', None)
                analysis_type = getattr(st.session_state, 'analysis_type', 'unknown')
                
                # Format timestamp
                if timestamp:
                    time_str = timestamp.strftime("%H:%M:%S")
                    date_str = timestamp.strftime("%Y-%m-%d")
                    
                    # Choose icon based on analysis type
                    type_icons = {
                        'initial': '🔍',
                        'fresh': '🔄',
                        'quick': '⚡'
                    }
                    icon = type_icons.get(analysis_type, '📊')
                    
                    st.info(f"**Patch {patch_info['patch']}** - Set {patch_info['set_number']}: {patch_info['set_name']} | {icon} Generated: {date_str} at {time_str}")
                else:
                    st.info(f"**Patch {patch_info['patch']}** - Set {patch_info['set_number']}: {patch_info['set_name']}")
                
                # Add regenerate options at the top of results
                st.markdown("##### 🔄 Regeneration Options")
                col_regen_fresh, col_regen_cached, col_download = st.columns([1, 1, 1])
                
                with col_regen_fresh:
                    if st.button("🔄 Fresh Analysis", type="secondary", use_container_width=True, help="Clear cache and get completely fresh data"):
                        # Create progress tracking
                        progress_placeholder = st.empty()
                        status_placeholder = st.empty()
                        
                        # Clear cache to ensure fresh data
                        cache_dir = Path("cache/riot_api")
                        if cache_dir.exists():
                            import shutil
                            shutil.rmtree(cache_dir)
                            cache_dir.mkdir(parents=True, exist_ok=True)
                            st.info("🗑️ Clearing cache for completely fresh data...")
                        
                        # Run the async analysis with progress updates
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            report, patch_info = loop.run_until_complete(run_analysis_with_progress(settings, progress_placeholder, status_placeholder))
                            
                            if report and patch_info:
                                # Clear progress indicators
                                progress_placeholder.empty()
                                status_placeholder.empty()
                                
                                # Store results in session state with timestamp
                                st.session_state.analysis_report = report
                                st.session_state.patch_info = patch_info
                                st.session_state.analysis_timestamp = datetime.now()
                                st.session_state.analysis_type = "fresh"
                                st.success("✅ Fresh analysis complete!")
                                st.rerun()
                        finally:
                            loop.close()
                
                with col_regen_cached:
                    if st.button("⚡ Quick Regen", use_container_width=True, help="Regenerate using cached data (faster)"):
                        # Create progress tracking
                        progress_placeholder = st.empty()
                        status_placeholder = st.empty()
                        
                        # Run the async analysis with progress updates (keep cache)
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            st.info("⚡ Using cached data for quick regeneration...")
                            report, patch_info = loop.run_until_complete(run_analysis_with_progress(settings, progress_placeholder, status_placeholder))
                            
                            if report and patch_info:
                                # Clear progress indicators
                                progress_placeholder.empty()
                                status_placeholder.empty()
                                
                                # Store results in session state with timestamp
                                st.session_state.analysis_report = report
                                st.session_state.patch_info = patch_info
                                st.session_state.analysis_timestamp = datetime.now()
                                st.session_state.analysis_type = "quick"
                                st.success("✅ Quick regeneration complete!")
                                st.rerun()
                        finally:
                            loop.close()
                
                with col_download:
                    # Download button for the report
                    st.download_button(
                        label="📥 Download Report",
                        data=st.session_state.analysis_report,
                        file_name=f"tft_analysis_patch_{patch_info['patch']}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                
                # Add helpful info about regeneration
                with st.expander("ℹ️ About Regeneration Options", expanded=False):
                    st.markdown("""
                    **🔄 Fresh Analysis**: Clears all cached data and fetches completely new match data from the API. Use this when:
                    - You want the most up-to-date challenger match data
                    - Significant time has passed since the last analysis  
                    - You suspect the meta has changed
                    
                    **⚡ Quick Regen**: Uses cached data but re-runs the AI analysis. Use this when:
                    - You want different AI insights from the same data
                    - The LLM analysis seems outdated or incomplete
                    - You want to experiment with different analysis angles
                    
                    **📥 Download Report**: Save the current analysis as a markdown file for offline viewing or sharing.
                    """)
                
                st.markdown("---")
                
                # Display the analysis report
                st.markdown(st.session_state.analysis_report)
            else:
                st.markdown("""
                *No analysis results yet. Click "Analyze Current Meta" to get started.*
                
                The analysis will:
                1. 🔍 Detect current TFT patch automatically
                2. 📊 Fetch recent challenger match data  
                3. 🤖 Use AI to extract team compositions
                4. 📈 Analyze performance patterns
                5. 📝 Generate strategic recommendations
                """)
    
    with tab2:
        # TFT Chat Tab
        st.header("💬 Ask the TFT Expert")
        st.markdown("*Chat with an AI that has access to real-time TFT data from the Riot API*")
        
        # Initialize chat history
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'chat_handler' not in st.session_state:
            try:
                llm_client = create_llm_client(settings)
                use_cache = getattr(settings, 'use_cache', False)
                riot_api = RiotTFTAPI(settings.riot_api_key, settings.riot_region, use_cache=use_cache)
                st.session_state.chat_handler = TFTChatHandler(llm_client, riot_api, settings)
            except Exception as e:
                st.error(f"Failed to initialize chat: {str(e)}")
                st.session_state.chat_handler = None
        
        # Chat interface
        if st.session_state.chat_handler:
            # Display suggested questions
            st.subheader("💡 Suggested Questions")
            
            # Get suggestions asynchronously
            if st.button("🔄 Get Fresh Suggestions"):
                with st.spinner("Getting suggestions based on current meta..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        suggestions = loop.run_until_complete(
                            st.session_state.chat_handler.suggest_questions()
                        )
                        st.session_state.suggestions = suggestions
                    finally:
                        loop.close()
            
            # Display suggestions
            if 'suggestions' in st.session_state:
                for suggestion in st.session_state.suggestions:
                    if st.button(suggestion, key=f"suggest_{suggestion[:30]}"):
                        # Use suggestion as input
                        st.session_state.pending_question = suggestion
                        st.rerun()
            
            # Chat messages display
            st.subheader("💬 Chat")
            
            # Display chat history
            chat_container = st.container(height=400)
            with chat_container:
                for message in st.session_state.chat_history:
                    with st.chat_message(message["role"]):
                        st.write(message["content"])
            
            # Handle pending question from suggestions
            user_input = None
            if 'pending_question' in st.session_state:
                user_input = st.session_state.pending_question
                del st.session_state.pending_question
            
            # Chat input
            if not user_input:
                user_input = st.chat_input("Ask me about TFT compositions, meta trends, strategies...")
            
            if user_input:
                # Add user message to history
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                # Get response from chat handler
                with st.spinner("Consulting TFT data..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        response = loop.run_until_complete(
                            st.session_state.chat_handler.handle_chat_message(
                                user_input, 
                                st.session_state.chat_history[:-1]  # Exclude the current message
                            )
                        )
                        
                        # Add assistant response to history
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                        st.rerun()
                    except Exception as e:
                        st.error(f"Chat error: {str(e)}")
                    finally:
                        loop.close()
            
            # Clear chat button
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
        
        else:
            st.error("Chat functionality is not available. Please check your API configuration.")
    
    # Footer
    st.markdown("---")
    st.markdown("*Powered by LangGraph workflows and LLM analysis of Riot Games API data*")


if __name__ == "__main__":
    main()