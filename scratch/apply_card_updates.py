import os

# 1. ProductDetailsModal.jsx
modal_path = r"c:\Users\haviprishiya\Downloads\update new\update\update\frontend\src\components\ProductDetailsModal.jsx"
with open(modal_path, 'r', encoding='utf-8') as f:
    m_content = f.read()

old_m_import = "import { Package, ImageOff, ShieldCheck, CheckCircle, AlertTriangle } from 'lucide-react';"
new_m_import = """import { Package, ImageOff, ShieldCheck, CheckCircle, AlertTriangle, Bookmark, Check } from 'lucide-react';
import { saveProduct } from '../services/api';"""
assert old_m_import in m_content, "old_m_import not found"
m_content = m_content.replace(old_m_import, new_m_import, 1)

old_m_rec = "const rec = product._recommendation;"
new_m_rec = """const rec = product._recommendation;
  const [isSaved, setIsSaved] = React.useState(false);

  const handleSaveProduct = async () => {
    try {
      const token = localStorage.getItem('trustrank_auth_token');
      await saveProduct(token, product);
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2500);
    } catch (e) {
      console.warn('Could not save product:', e);
    }
  };"""
assert old_m_rec in m_content, "old_m_rec not found"
m_content = m_content.replace(old_m_rec, new_m_rec, 1)

old_m_actions = """          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition"
          >
            Close Details
          </button>"""
new_m_actions = """          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={handleSaveProduct}
              className={`px-4 py-2.5 rounded-xl border text-xs font-bold transition flex items-center space-x-1.5 ${
                isSaved
                  ? 'bg-rose-50 border-rose-200 text-rose-600'
                  : 'border-slate-200 text-slate-700 hover:bg-slate-50'
              }`}
            >
              {isSaved ? <Check className="w-3.5 h-3.5 text-rose-600" /> : <Bookmark className="w-3.5 h-3.5 text-slate-500" />}
              <span>{isSaved ? 'Saved to Profile' : 'Save Product'}</span>
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold transition"
            >
              Close Details
            </button>
          </div>"""
assert old_m_actions in m_content, "old_m_actions not found"
m_content = m_content.replace(old_m_actions, new_m_actions, 1)

with open(modal_path, 'w', encoding='utf-8') as f:
    f.write(m_content)

print("ProductDetailsModal.jsx updated successfully!")

# 2. RecommendationCard.jsx
card_path = r"c:\Users\haviprishiya\Downloads\update new\update\update\frontend\src\components\RecommendationCard.jsx"
with open(card_path, 'r', encoding='utf-8') as f:
    c_content = f.read()

old_c_import = "import MarketplaceOffer from './MarketplaceOffer';"
new_c_import = """import MarketplaceOffer from './MarketplaceOffer';
import { saveProduct } from '../services/api';"""
assert old_c_import in c_content, "old_c_import not found"
c_content = c_content.replace(old_c_import, new_c_import, 1)

old_c_state = "const [imgIdx, setImgIdx] = useState(0);"
new_c_state = """const [imgIdx, setImgIdx] = useState(0);
  const [isSaved, setIsSaved] = useState(false);

  const handleSave = async (e) => {
    e.stopPropagation();
    try {
      const token = localStorage.getItem('trustrank_auth_token');
      await saveProduct(token, product);
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2500);
    } catch (err) {
      console.warn('Could not save product:', err);
    }
  };"""
assert old_c_state in c_content, "old_c_state not found"
c_content = c_content.replace(old_c_state, new_c_state, 1)

old_c_footer = """          <button
            type="button"
            onClick={() => onSelectProduct(product, recommendation)}
            className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1"
          >
            <span>View Full Specs & Review Sentiment</span>
            <svg className="w-4 h-4 ml-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>"""
new_c_footer = """          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={() => onSelectProduct(product, recommendation)}
              className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1"
            >
              <span>View Full Specs & Review Sentiment</span>
              <svg className="w-4 h-4 ml-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
              </svg>
            </button>
            <button
              type="button"
              onClick={handleSave}
              className={`p-1.5 rounded-lg border text-xs font-medium transition flex items-center space-x-1 ${
                isSaved
                  ? 'bg-rose-50 border-rose-200 text-rose-600 font-bold'
                  : 'border-slate-200 text-slate-500 hover:text-rose-600 hover:bg-rose-50/50'
              }`}
              title="Save to My Profile Bookmarks"
            >
              <svg className="w-3.5 h-3.5" fill={isSaved ? "currentColor" : "none"} viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
              </svg>
              <span>{isSaved ? 'Saved' : 'Save'}</span>
            </button>
          </div>"""
assert old_c_footer in c_content, "old_c_footer not found"
c_content = c_content.replace(old_c_footer, new_c_footer, 1)

with open(card_path, 'w', encoding='utf-8') as f:
    f.write(c_content)

print("RecommendationCard.jsx updated successfully!")
