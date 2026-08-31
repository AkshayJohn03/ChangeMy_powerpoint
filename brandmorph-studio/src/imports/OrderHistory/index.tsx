import svgPaths from "./svg-c89hd5wsk4";
import imgEllipse1 from "./5e119dcf1f143cd9e5345219c7fe1c81ba8b98c1.png";
import imgEllipse2 from "./d0d9a41422d64490087b6af23f2e5ff974e0596e.png";
import imgEllipse3 from "./938e718bb90442e82df8e1b43298eee580e8b30a.png";

function Frame1() {
  return (
    <div className="absolute content-stretch flex items-start left-[calc(25%+12.25px)] p-[10px] top-[666px]">
      <p className="[word-break:break-word] font-['Poppins:Medium',sans-serif] leading-[normal] not-italic relative shrink-0 text-[14px] text-center text-white whitespace-nowrap">Browse More Products</p>
    </div>
  );
}

function Group4() {
  return (
    <div className="[word-break:break-word] absolute contents leading-[normal] left-[61px] not-italic text-[#202020] text-center top-[73px] whitespace-nowrap">
      <p className="-translate-x-1/2 absolute font-['Poppins:SemiBold',sans-serif] left-[121.5px] text-[18px] top-[73px]">Order History</p>
      <p className="-translate-x-1/2 absolute font-['Poppins:Regular',sans-serif] left-[148px] text-[12px] top-[100px]">View Your previous purchase</p>
    </div>
  );
}

function SolarDangerTriangleBold() {
  return <div className="col-1 h-[7.481px] ml-[240.35px] mt-[120.76px] relative row-1 w-[9.284px]" data-name="solar:danger-triangle-bold" />;
}

function Group1() {
  return (
    <div className="col-1 grid-cols-[max-content] grid-rows-[max-content] inline-grid ml-0 mt-0 place-items-start relative row-1">
      <div className="bg-[#f1f1f1] col-1 h-[150px] ml-0 mt-0 relative rounded-[10px] row-1 shadow-[0px_2px_6px_0px_rgba(0,0,0,0.1)] w-[327px]" />
      <div className="bg-[#1c5d99] col-1 h-[33.13px] ml-[237.26px] mt-[18.17px] relative rounded-[5px] row-1 w-[73.24px]" />
      <SolarDangerTriangleBold />
    </div>
  );
}

function Group13() {
  return (
    <div className="[word-break:break-word] grid-cols-[max-content] grid-rows-[max-content] inline-grid leading-[0] not-italic place-items-start relative shrink-0">
      <p className="col-1 font-['Poppins:SemiBold',sans-serif] h-[20px] leading-[normal] ml-0 mt-0 relative row-1 text-[#202020] text-[12px] w-[144.416px]">High-waist green ...</p>
      <p className="col-1 font-['Poppins:Regular',sans-serif] h-[16.031px] leading-[normal] ml-0 mt-[18.54px] relative row-1 text-[#7c7c7c] text-[10px] text-center w-[73.24px]">Female - Pant</p>
    </div>
  );
}

function Frame9() {
  return (
    <div className="col-1 content-stretch flex gap-[8px] items-center ml-[15px] mt-[17.1px] relative row-1">
      <div className="relative shrink-0 size-[40px]">
        <img alt="" className="absolute block inset-0 max-w-none size-full" height="40" src={imgEllipse1} width="40" />
      </div>
      <Group13 />
    </div>
  );
}

function MdiCash() {
  return (
    <div className="relative shrink-0 size-[14px]" data-name="mdi:cash">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 14">
        <g id="mdi:cash">
          <path d={svgPaths.p18cb3f00} fill="var(--fill-0, #6B8620)" id="Vector" />
        </g>
      </svg>
    </div>
  );
}

function Frame2() {
  return (
    <div className="col-1 content-stretch flex gap-[3px] h-[16.923px] items-center ml-[8.56px] mt-0 relative row-1 w-[73.871px]">
      <MdiCash />
      <p className="[word-break:break-word] font-['Poppins:Regular',sans-serif] leading-[normal] not-italic relative shrink-0 text-[#878787] text-[8px] text-center whitespace-nowrap">Cash On Delivery</p>
    </div>
  );
}

function Group6() {
  return (
    <div className="grid-cols-[max-content] grid-rows-[max-content] inline-grid leading-[0] place-items-start relative shrink-0">
      <div className="bg-[#f1f1f1] col-1 h-[14px] ml-0 mt-[1.42px] relative rounded-[5px] row-1 w-[101px]" />
      <Frame2 />
    </div>
  );
}

function IconamoonDeliveryFastFill() {
  return (
    <div className="relative shrink-0 size-[9px]" data-name="iconamoon:delivery-fast-fill">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 9 9">
        <g clipPath="url(#clip0_1_2073)" id="iconamoon:delivery-fast-fill">
          <path clipRule="evenodd" d={svgPaths.p15ca1b40} fill="var(--fill-0, #A37531)" fillRule="evenodd" id="Vector" />
        </g>
        <defs>
          <clipPath id="clip0_1_2073">
            <rect fill="white" height="9" width="9" />
          </clipPath>
        </defs>
      </svg>
    </div>
  );
}

function Frame3() {
  return (
    <div className="content-stretch flex gap-[6px] items-center justify-center relative shrink-0">
      <IconamoonDeliveryFastFill />
      <p className="[word-break:break-word] font-['Poppins:Regular',sans-serif] leading-[normal] not-italic relative shrink-0 text-[#878787] text-[8px] text-center whitespace-nowrap">Status - Delivered</p>
    </div>
  );
}

function Frame6() {
  return (
    <div className="bg-[#f1f1f1] content-stretch flex flex-col h-[15px] items-center justify-center overflow-clip px-[5px] py-px relative rounded-[5px] shrink-0 w-[102px]">
      <Frame3 />
    </div>
  );
}

function Frame4() {
  return (
    <div className="content-stretch flex gap-[6px] items-center justify-center relative shrink-0">
      <div className="h-[6.75px] relative shrink-0 w-[7.5px]" data-name="Vector">
        <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 7.50018 6.75">
          <path clipRule="evenodd" d={svgPaths.p2bcaa70} fill="var(--fill-0, #F94747)" fillRule="evenodd" id="Vector" />
        </svg>
      </div>
      <p className="[word-break:break-word] font-['Poppins:Regular',sans-serif] leading-[normal] not-italic relative shrink-0 text-[#f94747] text-[8px] text-center whitespace-nowrap">Report An Issue</p>
    </div>
  );
}

function Frame5() {
  return (
    <div className="bg-[#f1f1f1] content-stretch flex flex-col h-[15px] items-center justify-center overflow-clip px-[6px] py-px relative rounded-[5px] shrink-0 w-[92px]">
      <Frame4 />
    </div>
  );
}

function Frame7() {
  return (
    <div className="col-1 content-stretch flex gap-[4px] h-[14.962px] items-center ml-0 mt-0 relative row-1 w-[305.338px]">
      <Group6 />
      <Frame6 />
      <Frame5 />
    </div>
  );
}

function Group10() {
  return (
    <div className="col-1 grid-cols-[max-content] grid-rows-[max-content] inline-grid ml-[6.19px] mt-[127.06px] place-items-start relative row-1">
      <Frame7 />
    </div>
  );
}

function Group7() {
  return (
    <div className="grid-cols-[max-content] grid-rows-[max-content] inline-grid place-items-start relative shrink-0">
      <Group1 />
      <p className="[word-break:break-word] col-1 font-['Poppins:SemiBold',sans-serif] h-[22.443px] leading-[normal] ml-[259.95px] mt-[24.58px] not-italic relative row-1 text-[#f1f1f1] text-[14px] text-center w-[27.852px]">₹60</p>
      <Frame9 />
      <div className="bg-[#d9d9d9] col-1 h-[32.061px] ml-0 mt-[118px] relative rounded-bl-[10px] rounded-br-[10px] row-1 w-[327px]" />
      <p className="[word-break:break-word] col-1 font-['Poppins:Regular',sans-serif] h-[36.336px] leading-[normal] ml-[15.47px] mt-[69px] not-italic relative row-1 text-[#7c7c7c] text-[10px] w-[300.18px]">The rich green colour adds a touch of sophistication and uniqueness to your wardrobe, making these pants .......</p>
      <Group10 />
    </div>
  );
}

function SolarDangerTriangleBold1() {
  return <div className="col-1 h-[7.481px] ml-[240.35px] mt-[120.76px] relative row-1 w-[9.284px]" data-name="solar:danger-triangle-bold" />;
}

function Group2() {
  return (
    <div className="col-1 grid-cols-[max-content] grid-rows-[max-content] inline-grid ml-0 mt-0 place-items-start relative row-1">
      <div className="bg-[#f1f1f1] col-1 h-[150px] ml-0 mt-0 relative rounded-[10px] row-1 shadow-[0px_2px_6px_0px_rgba(0,0,0,0.1)] w-[327px]" />
      <div className="bg-[#1c5d99] col-1 h-[33.13px] ml-[237.26px] mt-[18.17px] relative rounded-[5px] row-1 w-[73.24px]" />
      <SolarDangerTriangleBold1 />
    </div>
  );
}

function Group14() {
  return (
    <div className="col-1 grid-cols-[max-content] grid-rows-[max-content] inline-grid ml-0 mt-0 place-items-start relative row-1">
      <p className="[word-break:break-word] col-1 font-['Poppins:SemiBold',sans-serif] h-[19px] leading-[normal] ml-0 mt-0 not-italic relative row-1 text-[#202020] text-[12px] w-[156.795px]">Women’s Top com...</p>
    </div>
  );
}

function Group15() {
  return (
    <div className="grid-cols-[max-content] grid-rows-[max-content] inline-grid leading-[0] place-items-start relative shrink-0">
      <Group14 />
      <p className="[word-break:break-word] col-1 font-['Poppins:Regular',sans-serif] h-[16.031px] leading-[normal] ml-0 mt-[17.34px] not-italic relative row-1 text-[#7c7c7c] text-[10px] text-center w-[69.114px]">Female - Top</p>
    </div>
  );
}

function Frame10() {
  return (
    <div className="col-1 content-stretch flex gap-[8px] items-center ml-[15px] mt-[17.1px] relative row-1">
      <div className="relative shrink-0 size-[40px]">
        <img alt="" className="absolute block inset-0 max-w-none size-full" height="40" src={imgEllipse2} width="40" />
      </div>
      <Group15 />
    </div>
  );
}

function MdiCash1() {
  return (
    <div className="relative shrink-0 size-[14px]" data-name="mdi:cash">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 14">
        <g id="mdi:cash">
          <path d={svgPaths.p18cb3f00} fill="var(--fill-0, #6B8620)" id="Vector" />
        </g>
      </svg>
    </div>
  );
}

function Frame12() {
  return (
    <div className="col-1 content-stretch flex gap-[3px] h-[16.923px] items-center ml-[8.56px] mt-0 relative row-1 w-[73.871px]">
      <MdiCash1 />
      <p className="[word-break:break-word] font-['Poppins:Regular',sans-serif] leading-[normal] not-italic relative shrink-0 text-[#878787] text-[8px] text-center whitespace-nowrap">Cash On Delivery</p>
    </div>
  );
}

function Group9() {
  return (
    <div className="grid-cols-[max-content] grid-rows-[max-content] inline-grid leading-[0] place-items-start relative shrink-0">
      <div className="bg-[#f1f1f1] col-1 h-[14px] ml-0 mt-[1.42px] relative rounded-[5px] row-1 w-[101px]" />
      <Frame12 />
    </div>
  );
}

function IconamoonDeliveryFastFill1() {
  return (
    <div className="relative shrink-0 size-[9px]" data-name="iconamoon:delivery-fast-fill">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 9 9">
        <g clipPath="url(#clip0_1_2073)" id="iconamoon:delivery-fast-fill">
          <path clipRule="evenodd" d={svgPaths.p15ca1b40} fill="var(--fill-0, #A37531)" fillRule="evenodd" id="Vector" />
        </g>
        <defs>
          <clipPath id="clip0_1_2073">
            <rect fill="white" height="9" width="9" />
          </clipPath>
        </defs>
      </svg>
    </div>
  );
}

function Frame14() {
  return (
    <div className="content-stretch flex gap-[6px] items-center justify-center relative shrink-0">
      <IconamoonDeliveryFastFill1 />
      <p className="[word-break:break-word] font-['Poppins:Regular',sans-serif] leading-[normal] not-italic relative shrink-0 text-[#878787] text-[8px] text-center whitespace-nowrap">Status - Delivered</p>
    </div>
  );
}

function Frame13() {
  return (
    <div className="bg-[#f1f1f1] content-stretch flex flex-col h-[15px] items-center justify-center overflow-clip px-[5px] py-px relative rounded-[5px] shrink-0 w-[102px]">
      <Frame14 />
    </div>
  );
}

function Frame16() {
  return (
    <div className="content-stretch flex gap-[6px] items-center justify-center relative shrink-0">
      <div className="h-[6.75px] relative shrink-0 w-[7.5px]" data-name="Vector">
        <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 7.50018 6.75">
          <path clipRule="evenodd" d={svgPaths.p2bcaa70} fill="var(--fill-0, #F94747)" fillRule="evenodd" id="Vector" />
        </svg>
      </div>
      <p className="[word-break:break-word] font-['Poppins:Regular',sans-serif] leading-[normal] not-italic relative shrink-0 text-[#f94747] text-[8px] text-center whitespace-nowrap">Report An Issue</p>
    </div>
  );
}

function Frame15() {
  return (
    <div className="bg-[#f1f1f1] content-stretch flex flex-col h-[15px] items-center justify-center overflow-clip px-[6px] py-px relative rounded-[5px] shrink-0 w-[92px]">
      <Frame16 />
    </div>
  );
}

function Frame11() {
  return (
    <div className="col-1 content-stretch flex gap-[4px] h-[14.962px] items-center ml-0 mt-0 relative row-1 w-[305.338px]">
      <Group9 />
      <Frame13 />
      <Frame15 />
    </div>
  );
}

function Group11() {
  return (
    <div className="col-1 grid-cols-[max-content] grid-rows-[max-content] inline-grid ml-[6.19px] mt-[127.47px] place-items-start relative row-1">
      <Frame11 />
    </div>
  );
}

function Group8() {
  return (
    <div className="grid-cols-[max-content] grid-rows-[max-content] inline-grid place-items-start relative shrink-0">
      <Group2 />
      <p className="[word-break:break-word] col-1 font-['Poppins:SemiBold',sans-serif] h-[22.443px] leading-[normal] ml-[259.95px] mt-[24.58px] not-italic relative row-1 text-[#f1f1f1] text-[14px] text-center w-[27.852px]">₹80</p>
      <Frame10 />
      <div className="bg-[#d9d9d9] col-1 h-[32.061px] ml-0 mt-[118.2px] relative rounded-bl-[10px] rounded-br-[10px] row-1 w-[327px]" />
      <Group11 />
      <p className="[word-break:break-word] col-1 font-['Poppins:Regular',sans-serif] h-[36px] leading-[normal] ml-[17px] mt-[68.94px] not-italic relative row-1 text-[#7c7c7c] text-[10px] w-[299px]">Crafted from high-quality materials, these tops ensure durability and long-lasting wear. The soft and....</p>
    </div>
  );
}

function SolarDangerTriangleBold2() {
  return <div className="col-1 h-[7.481px] ml-[240.35px] mt-[120.76px] relative row-1 w-[9.284px]" data-name="solar:danger-triangle-bold" />;
}

function Group3() {
  return (
    <div className="col-1 grid-cols-[max-content] grid-rows-[max-content] inline-grid ml-0 mt-0 place-items-start relative row-1">
      <div className="bg-[#f1f1f1] col-1 h-[150px] ml-0 mt-0 relative rounded-[10px] row-1 shadow-[0px_2px_6px_0px_rgba(0,0,0,0.1)] w-[327px]" />
      <div className="bg-[#1c5d99] col-1 h-[33.13px] ml-[237.26px] mt-[18.17px] relative rounded-[5px] row-1 w-[73.24px]" />
      <SolarDangerTriangleBold2 />
    </div>
  );
}

function Group16() {
  return (
    <div className="[word-break:break-word] grid-cols-[max-content] grid-rows-[max-content] inline-grid leading-[0] not-italic place-items-start relative shrink-0">
      <p className="col-1 font-['Poppins:SemiBold',sans-serif] h-[19px] leading-[normal] ml-[1.03px] mt-0 relative row-1 text-[#202020] text-[12px] w-[145.448px]">LV blue top for wo...</p>
      <p className="col-1 font-['Poppins:Regular',sans-serif] h-[16.031px] leading-[normal] ml-0 mt-[18.14px] relative row-1 text-[#7c7c7c] text-[10px] text-center w-[73.24px]">Female - Top</p>
    </div>
  );
}

function Frame17() {
  return (
    <div className="col-1 content-stretch flex gap-[8px] items-center ml-[15px] mt-[17.68px] relative row-1">
      <div className="relative shrink-0 size-[40px]">
        <img alt="" className="absolute block inset-0 max-w-none size-full" height="40" src={imgEllipse3} width="40" />
      </div>
      <Group16 />
    </div>
  );
}

function MdiCash2() {
  return (
    <div className="relative shrink-0 size-[14px]" data-name="mdi:cash">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14 14">
        <g id="mdi:cash">
          <path d={svgPaths.p18cb3f00} fill="var(--fill-0, #6B8620)" id="Vector" />
        </g>
      </svg>
    </div>
  );
}

function Frame19() {
  return (
    <div className="col-1 content-stretch flex gap-[3px] h-[16.923px] items-center ml-[7.38px] mt-0 relative row-1 w-[63.631px]">
      <MdiCash2 />
      <p className="[word-break:break-word] font-['Poppins:Regular',sans-serif] leading-[normal] not-italic relative shrink-0 text-[#878787] text-[8px] text-center whitespace-nowrap">Paid Online</p>
    </div>
  );
}

function Group18() {
  return (
    <div className="grid-cols-[max-content] grid-rows-[max-content] inline-grid leading-[0] place-items-start relative shrink-0">
      <div className="bg-[#f1f1f1] col-1 h-[14px] ml-0 mt-[1.42px] relative rounded-[5px] row-1 w-[87px]" />
      <Frame19 />
    </div>
  );
}

function IconamoonDeliveryFastFill2() {
  return (
    <div className="relative shrink-0 size-[9px]" data-name="iconamoon:delivery-fast-fill">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 9 9">
        <g clipPath="url(#clip0_1_2073)" id="iconamoon:delivery-fast-fill">
          <path clipRule="evenodd" d={svgPaths.p15ca1b40} fill="var(--fill-0, #A37531)" fillRule="evenodd" id="Vector" />
        </g>
        <defs>
          <clipPath id="clip0_1_2073">
            <rect fill="white" height="9" width="9" />
          </clipPath>
        </defs>
      </svg>
    </div>
  );
}

function Frame21() {
  return (
    <div className="content-stretch flex gap-[6px] items-center justify-center relative shrink-0">
      <IconamoonDeliveryFastFill2 />
      <p className="[word-break:break-word] font-['Poppins:Regular',sans-serif] leading-[normal] not-italic relative shrink-0 text-[#878787] text-[8px] text-center whitespace-nowrap">Status - In Progress</p>
    </div>
  );
}

function Frame20() {
  return (
    <div className="bg-[#f1f1f1] content-stretch flex flex-col h-[15px] items-center justify-center overflow-clip px-[5px] py-px relative rounded-[5px] shrink-0 w-[102px]">
      <Frame21 />
    </div>
  );
}

function Frame23() {
  return (
    <div className="content-stretch flex gap-[6px] items-center justify-center relative shrink-0">
      <div className="h-[6.75px] relative shrink-0 w-[7.5px]" data-name="Vector">
        <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 7.50018 6.75">
          <path clipRule="evenodd" d={svgPaths.p2bcaa70} fill="var(--fill-0, #F94747)" fillRule="evenodd" id="Vector" />
        </svg>
      </div>
      <p className="[word-break:break-word] font-['Poppins:Regular',sans-serif] leading-[normal] not-italic relative shrink-0 text-[#f94747] text-[8px] text-center whitespace-nowrap">Report An Issue</p>
    </div>
  );
}

function Frame22() {
  return (
    <div className="bg-[#f1f1f1] content-stretch flex flex-col h-[15px] items-center justify-center overflow-clip px-[6px] py-px relative rounded-[5px] shrink-0 w-[92px]">
      <Frame23 />
    </div>
  );
}

function Frame18() {
  return (
    <div className="col-1 content-stretch flex gap-[4px] h-[14.962px] items-center ml-0 mt-0 relative row-1 w-[305.338px]">
      <Group18 />
      <Frame20 />
      <Frame22 />
    </div>
  );
}

function Group17() {
  return (
    <div className="col-1 grid-cols-[max-content] grid-rows-[max-content] inline-grid ml-[13.41px] mt-[127.68px] place-items-start relative row-1">
      <Frame18 />
    </div>
  );
}

function Group12() {
  return (
    <div className="grid-cols-[max-content] grid-rows-[max-content] inline-grid place-items-start relative shrink-0">
      <Group3 />
      <p className="[word-break:break-word] col-1 font-['Poppins:SemiBold',sans-serif] h-[22.443px] leading-[normal] ml-[259.95px] mt-[24.58px] not-italic relative row-1 text-[#f1f1f1] text-[14px] text-center w-[27.852px]">₹40</p>
      <Frame17 />
      <div className="bg-[#d9d9d9] col-1 h-[32.061px] ml-0 mt-[118.4px] relative rounded-bl-[10px] rounded-br-[10px] row-1 w-[327px]" />
      <Group17 />
      <p className="[word-break:break-word] col-1 font-['Poppins:Regular',sans-serif] h-[36.336px] leading-[normal] ml-[15.47px] mt-[68.68px] not-italic relative row-1 text-[#7c7c7c] text-[10px] w-[300.18px]">Discover our stylish Blue Fancy Top, a budget-friendly fashion gem at only 40rs. With its elegant ...</p>
    </div>
  );
}

function Frame8() {
  return (
    <div className="absolute content-stretch flex flex-col gap-[16px] items-center justify-center leading-[0] left-[24px] top-[151px] w-[327px]">
      <Group7 />
      <Group8 />
      <Group12 />
    </div>
  );
}

function Group() {
  return (
    <div className="absolute contents inset-0">
      <div className="absolute bg-[#1c5d99] inset-0 rounded-[15px]" />
    </div>
  );
}

function IconamoonSearchFill() {
  return (
    <button className="block cursor-pointer relative shrink-0 size-[20px]" data-name="iconamoon:search-fill">
      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20 20">
        <g id="iconamoon:search-fill">
          <path clipRule="evenodd" d={svgPaths.p3dacf400} fill="var(--fill-0, #F1F1F1)" fillRule="evenodd" id="Vector" />
        </g>
      </svg>
    </button>
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
      <IconamoonSearchFill />
      <div className="relative shrink-0 size-[20px]" data-name="Vector">
        <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20 20">
          <path clipRule="evenodd" d={svgPaths.p32f64900} fill="var(--fill-0, #639FAB)" fillRule="evenodd" id="Vector" />
        </svg>
      </div>
      <FluentCart24Filled />
    </div>
  );
}

function Group5() {
  return (
    <div className="absolute contents inset-[21.57%_10.7%_17.65%_11.27%]">
      <Frame />
      <button className="[word-break:break-word] absolute block cursor-pointer font-['Poppins:Light',sans-serif] inset-[64.71%_82.82%_17.65%_12.11%] leading-[0] not-italic text-[#f1f1f1] text-[6px] text-center whitespace-nowrap">
        <p className="leading-[normal]">Home</p>
      </button>
      <button className="[word-break:break-word] absolute block cursor-pointer font-['Poppins:Light',sans-serif] inset-[64.71%_58.31%_17.65%_35.77%] leading-[0] not-italic text-[6px] text-center text-white whitespace-nowrap">
        <p className="leading-[normal]">Search</p>
      </button>
      <p className="[word-break:break-word] absolute font-['Poppins:Light',sans-serif] inset-[64.71%_35.21%_17.65%_59.72%] leading-[normal] not-italic text-[#639fab] text-[6px] text-center whitespace-nowrap">Profile</p>
      <button className="[word-break:break-word] absolute block cursor-pointer font-['Poppins:Light',sans-serif] inset-[64.71%_10.7%_17.65%_82.82%] leading-[0] not-italic text-[6px] text-center text-white whitespace-nowrap">
        <p className="leading-[normal]">My Cart</p>
      </button>
    </div>
  );
}

export default function OrderHistory() {
  return (
    <div className="bg-[#f1f1f1] relative size-full" data-name="Order History">
      <div className="absolute bg-[#f1f1f1] h-[598px] left-0 top-[131px] w-[375px]" />
      <div className="absolute bg-[#1c5d99] h-[45px] left-[28px] rounded-[10px] top-[664px] w-[317px]" />
      <Frame1 />
      <Group4 />
      <div className="absolute h-[20px] left-[28px] top-[85px] w-[10px]">
        <div className="absolute inset-[-5.3%_-10.61%_-5.3%_-21.21%]">
          <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 13.182 22.1213">
            <path d={svgPaths.p70aad00} id="Vector 5" stroke="var(--stroke-0, #343434)" strokeWidth="3" />
          </svg>
        </div>
      </div>
      <Frame8 />
      <div className="absolute h-[51px] left-[10px] top-[742px] w-[355px]" data-name="Component 2">
        <Group />
        <Group5 />
      </div>
    </div>
  );
}