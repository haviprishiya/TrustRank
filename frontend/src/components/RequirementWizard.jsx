import React, { useState, useEffect } from 'react';
import Question from './Question';

export default function RequirementWizard({ intent, questions, onGenerate, onEditSearch, isLoading }) {
  const [answers, setAnswers] = useState({});

  useEffect(() => {
    // Initialize answers with defaults from questions or intent
    const initial = {};
    questions.forEach((q) => {
      if (q.default_value !== undefined && q.default_value !== null) {
        initial[q.id] = q.default_value;
      }
    });
    setAnswers(initial);
  }, [questions]);

  const handleAnswerChange = (questionId, value) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: value
    }));
  };

  const handleGenerate = () => {
    const budgetQuestion = questions.find((question) => question.id === 'budget');
    let minPrice = 0;
    let maxPrice = 0;
    const budgetVal = answers.budget;

    if (typeof budgetVal === 'object' && budgetVal !== null) {
      minPrice = Number(budgetVal.min || 0);
      maxPrice = Number(budgetVal.max || 0);
    } else if (typeof budgetVal === 'number') {
      maxPrice = budgetVal;
    }

    const budgetIsExplicit = Boolean(
      budgetQuestion && (
        (typeof budgetVal === 'object' && budgetVal !== null) ||
        (answers.budget !== undefined && answers.budget !== budgetQuestion.default_value)
      )
    );

    onGenerate({
      ...answers,
      budget: maxPrice || (typeof budgetVal === 'number' ? budgetVal : 0),
      min_price: minPrice,
      max_price: maxPrice,
      budget_is_explicit: budgetIsExplicit
    });
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Intent Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-indigo-950 rounded-2xl p-5 text-white shadow-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4 border border-slate-800">
        <div>
          <div className="flex items-center space-x-2">
            <span className="text-xs uppercase tracking-wider font-bold text-indigo-400">Search Intent Detected</span>
            <span className="text-xs px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-200 border border-indigo-500/30">
              {intent.category_display_name}
            </span>
          </div>
          {intent.extracted_requirements?.length > 0 && (
            <div className="text-xs text-emerald-200 mt-2">
              Requirement: {intent.extracted_requirements.join(' + ')}
            </div>
          )}
          <h2 className="text-xl sm:text-2xl font-bold mt-1 tracking-tight">
            Personalize requirements for <span className="text-indigo-300">"{intent.raw_query}"</span>
          </h2>
          <p className="text-xs text-slate-300 mt-1">
            Answer the dynamic questions below so TrustRank can evaluate real-world products against your exact needs.
          </p>
        </div>
        <button
          onClick={onEditSearch}
          className="self-start sm:self-center px-3.5 py-1.5 rounded-lg bg-slate-800/90 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition"
        >
          Change Query
        </button>
      </div>

      {/* Dynamic Questions List */}
      <div className="space-y-4">
        {questions.map((q) => (
          <Question
            key={q.id}
            question={q}
            value={answers[q.id]}
            onChange={handleAnswerChange}
          />
        ))}
      </div>

      {/* CTA Footer */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-lg flex flex-col sm:flex-row items-center justify-between gap-4 sticky bottom-4 z-30">
        <div>
          <div className="flex items-center space-x-2">
            <svg className="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
            </svg>
            <span className="text-sm font-bold text-slate-900">
              Ready to analyze live marketplace products
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Will query Amazon India, Flipkart, and verified providers in real-time.
          </p>
        </div>

        <button
          onClick={handleGenerate}
          disabled={isLoading}
          className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white font-bold text-sm sm:text-base shadow-lg shadow-indigo-500/25 transition-all flex items-center justify-center space-x-2"
        >
          {isLoading ? (
            <>
              <svg className="animate-spin -ml-1 mr-2 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
              <span>Querying Live Providers...</span>
            </>
          ) : (
            <>
              <span>Generate Recommendations</span>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </>
          )}
        </button>
      </div>
    </div>
  );
}
