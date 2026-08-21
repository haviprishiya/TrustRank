import React from 'react';

export default function Question({ question, value, onChange }) {
  const { id, question: title, subtext, type, options, min_value, max_value, step, unit } = question;

  const renderControl = () => {
    switch (type) {
      case 'range_slider': {
        const currentVal = value !== undefined ? Number(value) : (question.default_value || min_value || 0);
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-indigo-600">
                {unit || ''} {Number(currentVal).toLocaleString('en-IN')}
              </span>
              <span className="text-xs px-2.5 py-1 rounded-md bg-indigo-50 text-indigo-700 font-semibold border border-indigo-100">
                Target Budget
              </span>
            </div>
            <input
              type="range"
              min={min_value || 1000}
              max={max_value || 200000}
              step={step || 1000}
              value={currentVal}
              onChange={(e) => onChange(id, Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600 focus:outline-none"
            />
            <div className="flex justify-between text-xs text-slate-400 font-medium">
              <span>{unit || ''} {Number(min_value || 1000).toLocaleString('en-IN')}</span>
              <span>{unit || ''} {Number(max_value || 200000).toLocaleString('en-IN')}</span>
            </div>
          </div>
        );
      }

      case 'single_choice': {
        return (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {options.map((opt) => {
              const isSelected = value === opt.value;
              return (
                <div
                  key={opt.value}
                  onClick={() => onChange(id, opt.value)}
                  className={`p-3.5 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${
                    isSelected
                      ? 'bg-indigo-50/80 border-indigo-600 ring-2 ring-indigo-600/20 shadow-sm'
                      : 'bg-white border-slate-200 hover:border-indigo-200 hover:bg-slate-50/50'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <span className={`font-semibold text-sm ${isSelected ? 'text-indigo-950' : 'text-slate-900'}`}>
                      {opt.label}
                    </span>
                    {opt.badge && (
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ml-2 shrink-0 ${
                        isSelected ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600'
                      }`}>
                        {opt.badge}
                      </span>
                    )}
                  </div>
                  {opt.description && (
                    <p className="text-xs text-slate-500 mt-1 line-clamp-2">
                      {opt.description}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        );
      }

      case 'chip_select':
      case 'multi_choice': {
        const selectedList = Array.isArray(value) ? value : [];
        const toggleOption = (optVal) => {
          if (selectedList.includes(optVal)) {
            onChange(id, selectedList.filter((item) => item !== optVal));
          } else {
            onChange(id, [...selectedList, optVal]);
          }
        };

        return (
          <div className="flex flex-wrap gap-2">
            {options.map((opt) => {
              const isSelected = selectedList.includes(opt.value);
              return (
                <button
                  type="button"
                  key={opt.value}
                  onClick={() => toggleOption(opt.value)}
                  className={`px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all flex items-center space-x-1.5 ${
                    isSelected
                      ? 'bg-indigo-600 text-white border-indigo-600 shadow-sm shadow-indigo-600/20'
                      : 'bg-white text-slate-700 border-slate-200 hover:border-indigo-300 hover:bg-indigo-50/30'
                  }`}
                >
                  <span>{opt.label}</span>
                  {isSelected && (
                    <svg className="w-3.5 h-3.5 text-white ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </button>
              );
            })}
          </div>
        );
      }

      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-2xl p-5 sm:p-6 border border-slate-200/90 shadow-sm hover:shadow transition">
      <div className="mb-4">
        <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
          <span>{title}</span>
        </h3>
        {subtext && <p className="text-xs text-slate-500 mt-0.5">{subtext}</p>}
      </div>
      {renderControl()}
    </div>
  );
}
