import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import BatchListPage from "./pages/BatchListPage";
import BatchDetailPage from "./pages/BatchDetailPage";
import ReviewPage from "./pages/ReviewPage";
import SearchPage from "./pages/SearchPage";

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="navbar">
          <div className="nav-brand">BOAH AutoExtract</div>
          <div className="nav-links">
            <NavLink to="/">Batches</NavLink>
            <NavLink to="/upload">Upload</NavLink>
            <NavLink to="/search">Search</NavLink>
          </div>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<BatchListPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/batches/:batchId" element={<BatchDetailPage />} />
            <Route path="/review/:docId" element={<ReviewPage />} />
            <Route path="/search" element={<SearchPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
