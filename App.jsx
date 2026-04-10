import { useState, useEffect, useRef } from "react";
import axios from "axios";

const API = "https://python-project-backend-5.onrender.com";

export default function App() {

  // ---------- AUTH ----------
  const [user,setUser]=useState(null);
  const [username,setUsername]=useState("");
  const [password,setPassword]=useState("");

  // ---------- FORM ----------
  const [form,setForm]=useState({
    pregnancies:"",glucose:"",blood_pressure:"",
    skin_thickness:"",insulin:"",bmi:"",
    diabetes_pedigree:"",age:""
  });

  // ---------- RESULTS ----------
  const [result,setResult]=useState(null);
  const [graph,setGraph]=useState(null);
  const [shap,setShap]=useState(null);
  const [pie,setPie]=useState(null);
  const [trend,setTrend]=useState(null);

  // ---------- CHAT ----------
  const [chat,setChat]=useState([]);
  const [msg,setMsg]=useState("");
  const chatEndRef = useRef(null);

  useEffect(()=>{
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  },[chat]);

  // ---------- FUNCTIONS ----------
  const handleChange=(e)=>{
    setForm({...form,[e.target.name]:e.target.value});
  };

  const sendData=()=>{
    let d={};
    for(let k in form){
      let v=parseFloat(form[k]);
      if(isNaN(v)){ alert("Fill all fields"); return null; }
      d[k]=v;
    }
    return d;
  };

  const signup=async()=>{
    await axios.post(`${API}/signup`,{username,password});
    alert("Signup done");
  };

  const login=async()=>{
    const res=await axios.post(`${API}/login`,{username,password});
    if(res.data.user_id){
      setUser(res.data.user_id);
    }else{
      alert("Login failed");
    }
  };

  const predict=async()=>{
    const d=sendData(); if(!d) return;
    const res=await axios.post(`${API}/predict`,{...d,user_id:user});
    setResult(res.data);
  };

  const getGraph=async()=>{
    const d=sendData(); if(!d) return;
    await axios.post(`${API}/graph`,{...d,user_id:user});
    setGraph(`${API}/get-graph?${Date.now()}`);
  };

  const getShap=async()=>{
    const d=sendData(); if(!d) return;
    await axios.post(`${API}/shap`,{...d,user_id:user});
    setShap(`${API}/get-shap?${Date.now()}`);
  };

  const getPie=()=>setPie(`${API}/risk-chart?${Date.now()}`);
  const getTrend=()=>setTrend(`${API}/trend-chart?${Date.now()}`);

  const sendMessage=async()=>{
    if(!msg) return;

    setChat(prev=>[...prev,{text:msg,me:true}]);

    const res=await axios.post(`${API}/chat`,{
      user_id:user,
      message:msg
    });

    // typing effect
    setTimeout(()=>{
      setChat(prev=>[...prev,{text:res.data.reply,me:false}]);
    },500);

    setMsg("");
  };

  // ---------- LOGIN SCREEN ----------
  if(!user){
    return(
      <div style={{
        display:"flex",
        justifyContent:"center",
        alignItems:"center",
        height:"100vh",
        background:"#0f172a",
        color:"white"
      }}>
        <div style={{background:"#1e293b",padding:"40px",borderRadius:"12px"}}>
          <h1>MedAI Login</h1>

          <input placeholder="username"
            onChange={e=>setUsername(e.target.value)}
            style={inputStyle}
          />

          <input placeholder="password" type="password"
            onChange={e=>setPassword(e.target.value)}
            style={inputStyle}
          />

          <button style={btnStyle} onClick={login}>Login</button>
          <button style={btnStyle} onClick={signup}>Signup</button>
        </div>
      </div>
    );
  }

  // ---------- MAIN UI ----------
  return (
    <div style={{
      display:"flex",
      background:"#0f172a",
      color:"white",
      minHeight:"100vh"
    }}>

      {/* LEFT DASHBOARD */}
      <div style={{flex:3,padding:"20px"}}>

        <h1>MedAI Dashboard</h1>

        {/* INPUT GRID */}
        <div style={{
          display:"grid",
          gridTemplateColumns:"repeat(4,1fr)",
          gap:"10px"
        }}>
          {Object.keys(form).map(k=>(
            <input key={k}
              name={k}
              placeholder={k}
              onChange={handleChange}
              style={inputStyle}
            />
          ))}
        </div>

        <br/>

        {/* BUTTONS */}
        <div style={{display:"flex",gap:"10px",flexWrap:"wrap"}}>
          <button style={btnStyle} onClick={predict}>Predict</button>
          <button style={btnStyle} onClick={getGraph}>Graph</button>
          <button style={btnStyle} onClick={getShap}>SHAP</button>
          <button style={btnStyle} onClick={getPie}>Pie</button>
          <button style={btnStyle} onClick={getTrend}>Trend</button>
        </div>

        <br/>

        {/* RESULT CARD */}
        {result && (
          <div style={{
            background:"#1e293b",
            padding:"20px",
            borderRadius:"12px"
          }}>
            <h2>{result.risk_level} Risk</h2>

            <div style={{
              background:"#333",
              height:"20px",
              borderRadius:"10px"
            }}>
              <div style={{
                width:`${result.probability*100}%`,
                background:
                  result.risk_level==="Low"?"green":
                  result.risk_level==="Medium"?"orange":"red",
                height:"100%",
                borderRadius:"10px"
              }}></div>
            </div>

            <p>{Math.round(result.probability*100)}%</p>
          </div>
        )}

        <br/>

        {/* CHARTS */}
        <div style={{
          display:"grid",
          gridTemplateColumns:"repeat(2,1fr)",
          gap:"20px"
        }}>
          {graph && <img src={graph} width="100%" />}
          {shap && <img src={shap} width="100%" />}
          {pie && <img src={pie} width="100%" />}
          {trend && <img src={trend} width="100%" />}
        </div>

      </div>

      {/* RIGHT CHAT */}
      <div style={{
        flex:1,
        borderLeft:"1px solid #333",
        padding:"20px",
        display:"flex",
        flexDirection:"column"
      }}>

        <h2>AI Doctor</h2>

        <div style={{flex:1,overflowY:"auto"}}>
          {chat.map((c,i)=>(
            <div key={i} style={{
              textAlign:c.me?"right":"left",
              margin:"10px"
            }}>
              <span style={{
                background:c.me?"#3b82f6":"#374151",
                padding:"10px",
                borderRadius:"10px",
                display:"inline-block"
              }}>
                {c.text}
              </span>
            </div>
          ))}
          <div ref={chatEndRef}></div>
        </div>

        <div style={{display:"flex",gap:"5px"}}>
          <input
            value={msg}
            onChange={e=>setMsg(e.target.value)}
            style={{...inputStyle,flex:1}}
          />
          <button style={btnStyle} onClick={sendMessage}>Send</button>
        </div>

      </div>

    </div>
  );
}

// ---------- STYLES ----------
const inputStyle = {
  padding:"10px",
  borderRadius:"8px",
  border:"none",
  margin:"5px 0"
};

const btnStyle = {
  padding:"10px 15px",
  borderRadius:"8px",
  background:"linear-gradient(45deg,#3b82f6,#6366f1)",
  border:"none",
  color:"white",
  cursor:"pointer"
};