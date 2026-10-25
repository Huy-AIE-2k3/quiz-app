export function App() {
  return (
    <div className="min-h-screen bg-[#08090C] text-[#E5E7EB] flex flex-col items-center justify-center p-6">
      <div className="max-w-md w-full bg-[#101217] border border-[#1E222D] rounded-xl p-8 shadow-2xl text-center space-y-4">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#00FF88]/10 border border-[#00FF88]/30 text-[#00FF88] text-xs font-mono">
          <span className="w-2 h-2 rounded-full bg-[#00FF88] animate-pulse"></span>
          <span>MATHRIX SYSTEM ONLINE</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white font-mono">
          MATHRIX
        </h1>
        <p className="text-sm text-[#9CA3AF]">
          Nền tảng khảo thí trực tuyến môn Toán & Tin học
        </p>
        <div className="pt-4 border-t border-[#1E222D] flex justify-between text-xs font-mono text-[#9CA3AF]">
          <span>FastAPI Backend</span>
          <span className="text-[#00FF88]">Connected</span>
        </div>
      </div>
    </div>
  )
}

export default App
