import svgPaths from "./svg-bb46hhceia";
import imgRectangle109 from "./8daaa3cd46a5549c9cf01db65963c9f2a1a9cd4f.png";
import imgRectangle110 from "./4ad0057ebe9881f5ddabeecc98238abb3483c59f.png";

function PhCameraFill() {
  return (
    <div className="absolute left-[234px] size-[22px] top-[10px]" data-name="ph:camera-fill">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 22 22">
        <g id="ph:camera-fill">
          <path d={svgPaths.p229b8680} fill="var(--fill-0, #AFAFAF)" id="Vector" />
        </g>
      </svg>
    </div>
  );
}

function MaskGroup() {
  return (
    <div className="absolute inset-[30.95%_21.07%_26.29%_73.99%]" data-name="Mask group">
      <div className="absolute inset-[-5.57%_-7.29%]">
        <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 15.7161 19.9592">
          <g id="Mask group">
            <mask height="20" id="mask0_1_640" maskUnits="userSpaceOnUse" style={{ maskType: "luminance" }} width="16" x="0" y="0">
              <g id="Group">
                <g id="Group_2">
                  <path d={svgPaths.p96ae400} fill="var(--fill-0, white)" id="Vector" stroke="var(--stroke-0, white)" strokeLinejoin="round" strokeWidth="2" />
                  <path d={svgPaths.p14554100} id="Vector_2" stroke="var(--stroke-0, white)" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" />
                </g>
              </g>
            </mask>
            <g mask="url(#mask0_1_640)">
              <path d={svgPaths.p354117f0} fill="var(--fill-0, #AFAFAF)" id="Vector_3" />
            </g>
          </g>
        </svg>
      </div>
    </div>
  );
}

function Frame1() {
  return (
    <div className="bg-[#f1f1f1] h-[42px] overflow-clip relative rounded-[10px] shrink-0 w-[278px]">
      <p className="-translate-x-1/2 [word-break:break-word] absolute font-['Poppins:Regular',sans-serif] leading-[normal] left-[58px] not-italic text-[#7c7c7c] text-[8px] text-center top-[15px] whitespace-nowrap">Search For Products</p>
      <PhCameraFill />
      <MaskGroup />
    </div>
  );
}

function IconamoonSearchFill() {
  return (
    <div className="absolute left-[11px] size-[20px] top-[11px]" data-name="iconamoon:search-fill">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20 20">
        <g id="iconamoon:search-fill">
          <path clipRule="evenodd" d={svgPaths.p3dacf400} fill="var(--fill-0, #F1F1F1)" fillRule="evenodd" id="Vector" />
        </g>
      </svg>
    </div>
  );
}

function Frame2() {
  return (
    <div className="bg-[#1c5d99] content-stretch flex flex-col items-start justify-center overflow-clip p-[15px] relative rounded-[10px] shrink-0 size-[42px]">
      <IconamoonSearchFill />
    </div>
  );
}

function Frame3() {
  return (
    <div className="absolute content-stretch flex gap-[7px] items-start left-[24px] top-[109px] w-[327px]">
      <Frame1 />
      <Frame2 />
    </div>
  );
}

function Group2() {
  return (
    <div className="absolute contents left-[24px] top-[109px]">
      <Frame3 />
    </div>
  );
}

function Frame4() {
  return (
    <div className="absolute content-stretch flex gap-[10px] items-start left-[25px] top-[547px] w-[324px]">
      <div className="bg-[#1c5d99] h-[73px] relative rounded-[15px] shrink-0 w-[157px]" />
      <div className="bg-[#1c5d99] h-[73px] relative rounded-[15px] shrink-0 w-[157px]" />
      <p className="-translate-x-1/2 [word-break:break-word] absolute font-['Poppins:SemiBold',sans-serif] leading-[normal] left-[245px] not-italic text-[14px] text-center text-white top-[26px] whitespace-nowrap">Under ₹100</p>
    </div>
  );
}

function RightSide() {
  return (
    <div className="absolute h-[11.336px] right-[16.67px] top-[15.33px] w-[66.661px]" data-name="Right Side">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 66.6613 11.3359">
        <g id="Right Side">
          <g id="Battery">
            <path d={svgPaths.p39a0f980} id="Rectangle" opacity="0.35" stroke="var(--stroke-0, black)" />
            <path d={svgPaths.pc72ab80} fill="var(--fill-0, black)" id="Combined Shape" opacity="0.4" />
            <path d={svgPaths.pa39a400} fill="var(--fill-0, black)" id="Rectangle_2" />
          </g>
          <path clipRule="evenodd" d={svgPaths.pdda8a30} fill="var(--fill-0, black)" fillRule="evenodd" id="Wifi" />
          <path clipRule="evenodd" d={svgPaths.p3e2de00} fill="var(--fill-0, black)" fillRule="evenodd" id="Mobile Signal" />
        </g>
      </svg>
    </div>
  );
}

function StatusBarTime() {
  return (
    <div className="absolute h-[20px] left-[13px] rounded-[24px] top-[11px] w-[54px]" data-name="_StatusBar-time">
      <p className="-translate-x-1/2 [word-break:break-word] absolute font-['Poppins:Medium',sans-serif] h-[20px] leading-[20px] left-[27px] not-italic text-[15px] text-black text-center top-px tracking-[-0.5px] w-[54px]">9:41</p>
    </div>
  );
}

function LeftSide() {
  return (
    <div className="absolute contents left-[13px] top-[11px]" data-name="Left Side">
      <StatusBarTime />
    </div>
  );
}

function Group4() {
  return (
    <div className="absolute contents left-[13px] top-[11px]">
      <RightSide />
      <LeftSide />
    </div>
  );
}

function Group5() {
  return (
    <div className="absolute contents left-[13px] top-[11px]">
      <Group4 />
      <div className="absolute bg-[#202020] h-[20px] left-[calc(25%+42.25px)] rounded-[40px] top-[11px] w-[100px]" />
    </div>
  );
}

function Group() {
  return (
    <div className="absolute contents left-[24px] top-[201px]">
      <div className="absolute bg-[#639fab] h-[50px] left-[24px] rounded-[10px] top-[201px] w-[155.437px]" />
      <div className="absolute bg-[#639fab] h-[50px] left-[24px] rounded-[10px] top-[259px] w-[155.437px]" />
      <div className="absolute bg-[#639fab] h-[50px] left-[calc(50%+8.06px)] rounded-[10px] top-[201px] w-[155.437px]" />
      <div className="absolute bg-[#639fab] h-[50px] left-[calc(50%+8.06px)] rounded-[10px] top-[259px] w-[155.437px]" />
    </div>
  );
}

function Group1() {
  return (
    <div className="absolute contents inset-0">
      <div className="absolute bg-[#1c5d99] inset-0 rounded-[15px]" />
    </div>
  );
}

function IconamoonSearchFill1() {
  return (
    <div className="relative shrink-0 size-[20px]" data-name="iconamoon:search-fill">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20 20">
        <g id="iconamoon:search-fill">
          <path clipRule="evenodd" d={svgPaths.p3dacf400} fill="var(--fill-0, #639FAB)" fillRule="evenodd" id="Vector" />
        </g>
      </svg>
    </div>
  );
}

function FluentCart24Filled() {
  return (
    <button className="block cursor-pointer relative shrink-0 size-[20px]" data-name="fluent:cart-24-filled">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20 20">
        <g clipPath="url(#clip0_1_627)" id="fluent:cart-24-filled">
          <path d={svgPaths.p12c47330} fill="var(--fill-0, #F1F1F1)" id="Vector" />
        </g>
        <defs>
          <clipPath id="clip0_1_627">
            <rect fill="white" height="20" width="20" />
          </clipPath>
        </defs>
      </svg>
    </button>
  );
}

function Frame() {
  return (
    <div className="absolute content-stretch flex gap-[64px] inset-[21.57%_11.17%_39.22%_11.27%] items-center justify-center">
      <button className="block cursor-pointer h-[20px] relative shrink-0 w-[23.333px]" data-name="Vector">
        <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 23.3333 20">
          <path d={svgPaths.p26fe1880} fill="var(--fill-0, #F1F1F1)" id="Vector" />
        </svg>
      </button>
      <IconamoonSearchFill1 />
      <button className="block cursor-pointer relative shrink-0 size-[20px]" data-name="Vector">
        <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20 20">
          <path clipRule="evenodd" d={svgPaths.p32f64900} fill="var(--fill-0, #F1F1F1)" fillRule="evenodd" id="Vector" />
        </svg>
      </button>
      <FluentCart24Filled />
    </div>
  );
}

function Group3() {
  return (
    <div className="absolute contents inset-[21.57%_10.7%_17.65%_11.27%]">
      <Frame />
      <button className="[word-break:break-word] absolute block cursor-pointer font-['Poppins:Light',sans-serif] inset-[64.71%_82.82%_17.65%_12.11%] leading-[0] not-italic text-[#f1f1f1] text-[6px] text-center whitespace-nowrap">
        <p className="leading-[normal]">Home</p>
      </button>
      <p className="[word-break:break-word] absolute font-['Poppins:Light',sans-serif] inset-[64.71%_58.31%_17.65%_35.77%] leading-[normal] not-italic text-[#639fab] text-[6px] text-center whitespace-nowrap">Search</p>
      <button className="[word-break:break-word] absolute block cursor-pointer font-['Poppins:Light',sans-serif] inset-[64.71%_10.7%_17.65%_82.82%] leading-[0] not-italic text-[6px] text-center text-white whitespace-nowrap">
        <p className="leading-[normal]">My Cart</p>
      </button>
    </div>
  );
}

export default function Search() {
  return (
    <div className="bg-white relative size-full" data-name="Search">
      <Group2 />
      <Frame4 />
      <p className="-translate-x-1/2 [word-break:break-word] absolute font-['Poppins:SemiBold',sans-serif] leading-[normal] left-[99.5px] not-italic text-[14px] text-center text-white top-[571px] whitespace-nowrap">Under ₹50</p>
      <div className="absolute bg-[#1c5d99] h-[73px] left-[25px] rounded-[15px] top-[630px] w-[157px]" />
      <div className="absolute bg-[#1c5d99] h-[73px] left-[calc(50%+4.5px)] rounded-[15px] top-[630px] w-[157px]" />
      <p className="-translate-x-1/2 [word-break:break-word] absolute font-['Poppins:SemiBold',sans-serif] leading-[normal] left-[101px] not-italic text-[14px] text-center text-white top-[656px] whitespace-nowrap">Under ₹500</p>
      <p className="-translate-x-1/2 [word-break:break-word] absolute font-['Poppins:SemiBold',sans-serif] leading-[normal] left-[calc(50%+83px)] not-italic text-[14px] text-center text-white top-[656px] whitespace-nowrap">Under ₹1000</p>
      <div className="absolute h-[135px] left-[25px] rounded-[10px] top-[356px] w-[327px]">
        <div aria-hidden className="absolute inset-0 pointer-events-none rounded-[10px]">
          <div className="absolute bg-[#d9d9d9] inset-0 rounded-[10px]" />
          <img alt="" className="absolute max-w-none object-cover rounded-[10px] size-full" src={imgRectangle109} />
        </div>
      </div>
      <div className="absolute bg-[#1c5d99] h-[135px] left-[25px] opacity-60 rounded-[10px] top-[356px] w-[327px]" />
      <div className="absolute h-[135px] left-[calc(100%-15px)] rounded-[10px] top-[356px] w-[320px]">
        <div aria-hidden className="absolute inset-0 pointer-events-none rounded-[10px]">
          <div className="absolute bg-[#d9d9d9] inset-0 rounded-[10px]" />
          <img alt="" className="absolute max-w-none object-cover rounded-[10px] size-full" src={imgRectangle110} />
        </div>
      </div>
      <Group5 />
      <Group />
      <p className="-translate-x-1/2 [word-break:break-word] absolute font-['Poppins:SemiBold',sans-serif] leading-[normal] left-[83px] not-italic text-[12px] text-black text-center top-[167px] whitespace-nowrap">Popular Categories</p>
      <p className="-translate-x-1/2 [word-break:break-word] absolute font-['Poppins:SemiBold',sans-serif] leading-[normal] left-[75.5px] not-italic text-[12px] text-black text-center top-[328px] whitespace-nowrap">Featured For You</p>
      <p className="-translate-x-1/2 [word-break:break-word] absolute font-['Poppins:SemiBold',sans-serif] leading-[normal] left-[62px] not-italic text-[12px] text-black text-center top-[513px] whitespace-nowrap">Sort By Price</p>
      <p className="-translate-x-1/2 [text-decoration-skip-ink:none] [text-underline-position:from-font] [word-break:break-word] absolute decoration-from-font decoration-solid font-['Poppins:SemiBold',sans-serif] leading-[normal] left-[calc(87.5%+4.88px)] not-italic text-[#343434] text-[8px] text-center top-[173px] underline whitespace-nowrap">View All</p>
      <p className="-translate-x-1/2 [word-break:break-word] absolute font-['Poppins:SemiBold',sans-serif] leading-[normal] left-[99.5px] not-italic text-[12px] text-center text-white top-[216px] whitespace-nowrap">Female Top</p>
      <p className="-translate-x-1/2 [word-break:break-word] absolute font-['Poppins:SemiBold',sans-serif] leading-[normal] left-[99px] not-italic text-[12px] text-center text-white top-[274px] whitespace-nowrap">Saree</p>
      <p className="-translate-x-1/2 [word-break:break-word] absolute font-['Poppins:SemiBold',sans-serif] leading-[normal] left-[calc(50%+83.5px)] not-italic text-[12px] text-center text-white top-[274px] whitespace-nowrap">Party wear</p>
      <p className="-translate-x-1/2 [word-break:break-word] absolute font-['Poppins:SemiBold',sans-serif] leading-[normal] left-[calc(50%+82.5px)] not-italic text-[12px] text-center text-white top-[216px] whitespace-nowrap">Accessories</p>
      <p className="-translate-x-1/2 [word-break:break-word] absolute font-['Poppins:SemiBold',sans-serif] leading-[normal] left-[calc(25%+88.25px)] not-italic text-[16px] text-center text-white top-[408px] whitespace-nowrap">Accessories</p>
      <div className="absolute bg-[#1c5d99] h-[135px] left-[calc(100%-15px)] opacity-60 rounded-[10px] top-[356px] w-[327px]" />
      <div className="-translate-x-1/2 absolute bottom-[18px] h-[51px] left-1/2 w-[355px]" data-name="Component 1">
        <Group1 />
        <p className="[word-break:break-word] absolute font-['Poppins:Light',sans-serif] inset-[64.71%_35.21%_17.65%_59.72%] leading-[normal] not-italic text-[6px] text-center text-white whitespace-nowrap">Profile</p>
        <Group3 />
      </div>
      <div className="absolute bg-[#f1f1f1] h-[48px] left-[24px] overflow-clip rounded-[10px] top-[53px] w-[327px]" data-name="Frame 8/Default">
        <div className="absolute bg-[#1c5d99] h-[42px] left-[3px] rounded-[8px] top-[3px] w-[157px]" />
        <p className="[word-break:break-word] absolute font-['Poppins:Bold',sans-serif] leading-[normal] left-[65px] not-italic text-[#f1f1f1] text-[12px] top-[16px] whitespace-nowrap">Shop</p>
        <p className="[word-break:break-word] absolute font-['Poppins:Regular',sans-serif] leading-[normal] left-[224px] not-italic text-[#343434] text-[12px] top-[16px] whitespace-nowrap">NGO</p>
      </div>
    </div>
  );
}