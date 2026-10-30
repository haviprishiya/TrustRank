import React from 'react';

export default function Question({ question, value, onChange }) {
  const { id, question: title, subtext, type, options, min_value, max_value, step, unit } = question;

  const renderControl = () => {
    switch (type) {
      case 'range_slider': {
        const minLimit = Number(min_value || 1000);
        const maxLimit = Number(max_value || 200000);
        const stepVal = Number(step || 1000);

        let currentMin = minLimit;
        let currentMax = Number(question.default_value || maxLimit);

        if (typeof value === 'object' && value !== null) {
          if (value.min !== undefined) currentMin = Number(value.min);
          if (value.max !== undefined) currentMax = Number(value.max);
        } else if (typeof value === 'number') {
          currentMax = Number(value);
        }

        const handleMinChange = (newMin) => {
          const clampedMin = Math.min(Math.max(newMin, minLimit), currentMax - stepVal);
          onChange(id, { min: clampedMin, max: currentMax });
        };

        const handleMaxChange = (newMax) => {
          const clampedMax = Math.max(Math.min(newMax, maxLimit), currentMin + stepVal);
          onChange(id, { min: currentMin, max: clampedMax });
        };

        return (
          <div className="space-y-4 bg-slate-50/80 p-4 rounded-xl border border-slate-200/90 shadow-sm">
            {/* Range Banner */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <span className="text-[11px] uppercase tracking-wider text-slate-500 font-bold block mb-0.5">
                  Selected Price Range
                </span>
                <div className="flex items-center space-x-2">
                  <span className="text-xl sm:text-2xl font-black text-indigo-700 tracking-tight">
                    {unit || '₹'}{Number(currentMin).toLocaleString('en-IN')}
                  </span>
                  <span className="text-slate-400 font-bold text-sm sm:text-base">to</span>
                  <span className="text-xl sm:text-2xl font-black text-indigo-700 tracking-tight">
                    {unit || '₹'}{Number(currentMax).toLocaleString('en-IN')}
                  </span>
                </div>
              </div>
              <span className="self-start sm:self-center text-xs px-3 py-1 rounded-full bg-indigo-100/90 text-indigo-800 font-bold border border-indigo-200">
                Min — Max Filter
              </span>
            </div>

            {/* Direct Number Input Fields */}
            <div className="grid grid-cols-2 gap-3 pt-1">
              <div>
                <label className="text-[11px] font-bold uppercase text-slate-600 block mb-1">
                  Minimum Price
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2.5 text-xs font-bold text-slate-400">
                    {unit || '₹'}
                  </span>
                  <input
                    type="number"
                    min={minLimit}
                    max={currentMax - stepVal}
                    step={stepVal}
                    value={currentMin}
                    onChange={(e) => handleMinChange(Number(e.target.value))}
                    className="w-full pl-7 pr-3 py-2 text-sm font-bold bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 text-slate-900 shadow-sm"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-bold uppercase text-slate-600 block mb-1">
                  Maximum Price
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2.5 text-xs font-bold text-slate-400">
                    {unit || '₹'}
                  </span>
                  <input
                    type="number"
                    min={currentMin + stepVal}
                    max={maxLimit}
                    step={stepVal}
                    value={currentMax}
                    onChange={(e) => handleMaxChange(Number(e.target.value))}
                    className="w-full pl-7 pr-3 py-2 text-sm font-bold bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 text-slate-900 shadow-sm"
                  />
                </div>
              </div>
            </div>

            {/* Dual Sliders */}
            <div className="space-y-3 pt-1">
              <div>
                <div className="flex justify-between text-[11px] font-semibold text-slate-500 mb-1">
                  <span>Min: {unit || '₹'}{Number(currentMin).toLocaleString('en-IN')}</span>
                  <span>Floor: {unit || '₹'}{Number(minLimit).toLocaleString('en-IN')}</span>
                </div>
                <input
                  type="range"
                  min={minLimit}
                  max={currentMax - stepVal}
                  step={stepVal}
                  value={currentMin}
                  onChange={(e) => handleMinChange(Number(e.target.value))}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600 focus:outline-none"
                />
              </div>

              <div>
                <div className="flex justify-between text-[11px] font-semibold text-slate-500 mb-1">
                  <span>Max: {unit || '₹'}{Number(currentMax).toLocaleString('en-IN')}</span>
                  <span>Ceiling: {unit || '₹'}{Number(maxLimit).toLocaleString('en-IN')}</span>
                </div>
                <input
                  type="range"
                  min={currentMin + stepVal}
                  max={maxLimit}
                  step={stepVal}
                  value={currentMax}
                  onChange={(e) => handleMaxChange(Number(e.target.value))}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600 focus:outline-none"
                />
              </div>
            </div>

            <div className="flex justify-between text-[10px] text-slate-400 font-medium">
              <span>Catalog Minimum: {unit || '₹'} {Number(minLimit).toLocaleString('en-IN')}</span>
              <span>Catalog Maximum: {unit || '₹'} {Number(maxLimit).toLocaleString('en-IN')}</span>
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
