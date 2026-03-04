;----------------------------------------------------------------------
; Output_seeding_criteria_CONUS_WYOCLIMO_AIR.ncl
;
;  Project : WYO precipitation and cloud seedibility study 
;
;  Purpose :
;            This is an NCL file for preparing 700 hPa level data from 
;            CONUS CTRL run.
;
;  Remarks : 1) Froude number computation is set up for each
;				range differently becaues of
;               range height and orientation.
;            2) U and V are rotated appropriately.
;            3) Instead of reading RAINNC + I_RAINNC and SNOWNC, this code
;               reads PREC_ACC_NC and SNOW_ACC_NC (hourly accumulation
;               as oppose to accumulation from model init)
;
; Usage    : ncl 'year =2000 month=01' output_seedingcriteria_IDWR.ncl
;
; Original Code from Lulin.  Modified by Kyoko Ikeda 6 December 2017
; Modified for IDWR by Courtney Weeks 6 October 2021
;            
;----------------------------------------------------------------------

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/shea_util.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/wrf/WRFUserARW.ncl"

begin
;*********************************************************;
;                    static variables                     ;
;*********************************************************;
; run = "PGW"
indir="/glade/derecho/scratch/meghan/Roza/data/CONUS404/cut/"
indir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/cut/"
; outdir="/glade/derecho/scratch/meghan/Roza/data/CONUS404/SeedingVariables/"
outdir="/glade/campaign/ral/hap/meghan/Roza/data/CONUS404/SeedingVariables/"
month = sprinti("%0.2i",mm)
; Coefficients for water saturation ratio and ice saturation ratio
  cst=(/.609868993E03,.499320233E02,.184672631E01,.402737184E-1,.565392987E-3,.521693933E-5,.307839583E-7,.105785160E-9,.161444444E-12/)

; Thermodynamic constants
  t0=273.16
  c_pd=1005.0
  m_air=0.0289644
  r_d=287.05
  r_gas=8.316963
  l_v=2.501e6
  l_s=2.834e6
  g=9.80665

; Pi; later would add phi for mtn ranges to calc Fr once we know what ranges to use
  pi=3.1415926535897932384626433   
  phi_UIN=pi
  phi_BRR=0.
  phi_SRR=0.

; AGL levels for GS MC
  h_gmc=1000
  ; h_gmc2=2100
  delta_hg=50
  ; h_l1 = 3500
  ; h_h1 = 4500
  h_l1 = 2500
  h_h1 = 3500

;*********************************************************;
;                    Algorithm                            ;
;*********************************************************;

  ; f3d=systemfunc("/bin/ls -1 " + indir + "wrf3d*_" + year + "-" + month + "*")
  f3d=systemfunc("/usr/bin/find " + indir + " -name 'wrf3d*_" + year + "-" + month + "*.nc'")

  nfile=dimsizes(f3d)-1
  do nf=0, nfile

; Open files for precipitation distraction
    af=f3d(nf)
    a = addfile(af,"r")
    bf = str_sub_str(af,"/wrf3d","/2d/wrf2d")
    b = addfile(bf,"r")
    Time = a->XTIME;
    time_vec := cd_calendar( Time(0) , 0)
	
	; Start time loop to calcualte all MC and DC in each record over the entire domain
    time_stamp := sprinti("%0.4i", tointeger(time_vec(0,0))) + "-" \
                + sprinti("%0.2i", tointeger(time_vec(0,1))) + "-" \
                + sprinti("%0.2i", tointeger(time_vec(0,2))) + "_" \
                + sprinti("%0.2i", tointeger(time_vec(0,3))) + "0000"
    print("Working on time: " + time_stamp )

    print( " wrf3d " + af )

    print( " ... processing " ) 
    print( " " ) 
	
	cf = outdir + "Seeding_criteria_"+ time_stamp +".nc"
	
	if (fileexists(cf)) then
		print("File exists. Next file ... ")
		continue
	end if

; mdims(0) = time, mdims(1) = z, mdims(2) = y, mdims(3) = x
    mdims = getfilevardimsizes(a,"QVAPOR") ; get some dimension sizes for the file

    ter = a->Z(:,0,:,:)*1. ;wrf_user_getvar(a,"HGT",0)           ; Read the variable to memory
    index=ter
    index@_FillValue=-999.0

; Full level height in m
    hgt=1.*a->Z ;(wrf_user_getvar(a,"PHB",0)+wrf_user_getvar(a,"PH",0))/g
; Half level height (mass center)
    height=(hgt(:,1:mdims(1),:,:)+hgt(:,0:mdims(1)-1,:,:))*0.5 ;wrf_user_getvar(a,"height",0)
    height_agl=height
    height_agl=0.
    dz=height_agl

; Variable used for interpolation (both AMSL and AGL)
    do k=0,mdims(1)-1
      height_agl(:,k,:,:)=height(:,k,:,:)-ter
      dz(:,k,:,:)=hgt(:,k+1,:,:)-hgt(:,k,:,:)
    end do

    index_hagl=where(height_agl.lt.h_gmc+delta_hg,1.,-999.)
    index_hagl@_FillValue=-999.

    ; index_hagl2=where(height_agl.lt.h_gmc2+delta_hg,1.,-999.)
    ; index_hagl2@_FillValue=-999.

    index_hasl=where(height.gt.h_l1-delta_hg .and. height.lt.h_h1+delta_hg,1.,-999.)
    index_hasl@_FillValue=-999.

; Records in file  
   ;times  = wrf_user_list_times(a)

; CTT CBH CDP
    ; top_index= new((/mdims(0),mdims(1),mdims(2),mdims(3)/),float)
    ; top_index = top_index@_FillValue
    ; base_index = top_index

    ; CTT = new((/mdims(0),mdims(2),mdims(3)/),float)
    ; CTT = CTT@_FillValue
    ; CDP = CTT
    ; CBH = CTT

; Initialize the target mask
    index=1.

; Hydrometeors for MC
    p=a->P ;(0,:,:,:) ; total pressure
    tk=a->TK ;(0,:,:,:)
    tc=tk-273.15
    rho=p/(tk*287.5) ;1./wrf_user_getvar(a,"ALT",0)
    z=a->Z(:,1:mdims(1),:,:)
    
    ; index_250mb=where(abs(p*0.01-250).lt.15.,1.,-999.)
    ; index_250mb@_FillValue=-999.

    ; index_500mb=where(abs(p*0.01-500).lt.15.,1.,-999.)
    ; index_500mb@_FillValue=-999.

    index_700mb=where(abs(p*0.01-700).lt.15.,1.,-999.)
    index_700mb@_FillValue=-999.

    ; index_850mb=where(abs(p*0.01-850).lt.15.,1.,-999.)
    ; index_850mb@_FillValue=-999.


    ; tc_250mb=dim_avg_n(tc*index_250mb,1)
    ; tc_250mb@_FillValue=-999.

    ; z_250mb=dim_avg_n(z*index_250mb,1)
    ; z_250mb@_FillValue=-999.



    ; tc_500mb=dim_avg_n(tc*index_500mb,1)
    ; tc_500mb@_FillValue=-999.

    ; z_500mb=dim_avg_n(z*index_500mb,1)
    ; z_500mb@_FillValue=-999.

    tc_700mb=dim_avg_n(tc*index_700mb,1)
    tc_700mb@_FillValue=-999.

    z_700mb=dim_avg_n(z*index_700mb,1)
    z_700mb@_FillValue=-999.


    lw=wrf_user_getvar(a,"QCLOUD",-1)+wrf_user_getvar(a,"QRAIN",-1)
    qw=rho*lw
    qice=wrf_user_getvar(a,"QICE",-1)+wrf_user_getvar(a,"QSNOW",-1)+wrf_user_getvar(a,"QGRAUP",-1)
    qt=lw+wrf_user_getvar(a,"QICE",-1)+wrf_user_getvar(a,"QSNOW",-1)+wrf_user_getvar(a,"QGRAUP",-1)
    
    _qcloud=wrf_user_getvar(a,"QCLOUD",-1)
    qcloud=dim_avg_n(_qcloud,1)
    qcloud@_FillValue=-999.

    _qrain=wrf_user_getvar(a,"QRAIN",-1)
    qrain=dim_avg_n(_qrain,1)
    qrain@_FillValue=-999.

    __qice=wrf_user_getvar(a,"QICE",-1)
    _qice=dim_avg_n(__qice,1)
    _qice@_FillValue=-999.

    _qsnow=wrf_user_getvar(a,"QSNOW",-1)
    qsnow=dim_avg_n(_qsnow,1)
    qsnow@_FillValue=-999.

    _qgraup=wrf_user_getvar(a,"QGRAUP",-1)
    qgraup=dim_avg_n(_qgraup,1)
    qgraup@_FillValue=-999.

    _qvapor=wrf_user_getvar(a,"QVAPOR",-1)
    qvapor=dim_avg_n(_qvapor,1)
    qvapor@_FillValue=-999.

    index_qt=where(qt.ge. 1.e-6, 1., 0.)
    ; tc_850mb=dim_avg_n(tc*index_850mb,1)
    ; tc_850mb@_FillValue=-999.

    ; z_850mb=dim_avg_n(z*index_850mb,1)
    ; z_850mb@_FillValue=-999.

    ; lw=wrf_user_getvar(a,"QCLOUD",-1)+wrf_user_getvar(a,"QRAIN",-1)
    ; qw=rho*lw
    ; qice=wrf_user_getvar(a,"QICE",-1)+wrf_user_getvar(a,"QSNOW",-1)+wrf_user_getvar(a,"QGRAUP",-1)
    ; qt=lw+wrf_user_getvar(a,"QICE",-1)+wrf_user_getvar(a,"QSNOW",-1)+wrf_user_getvar(a,"QGRAUP",-1)

    ; index_qt=where(qt.ge. 1.e-6, 1., 0.)

;      do xx = 0,mdims(3)-1
;         do yy = 0,mdims(2)-1

;            zz =0
;            ;if there is cloud in this column
;            temp = sum(index_qt(0,:,yy,xx))
;            do while(temp .gt. 0.5)

;               ;cloud base
;               do while(index_qt(0,zz,yy,xx) .lt. 0.5 .and. zz .lt.mdims(1)-1)
;                  zz=zz+1
;               end do

;               if (zz .lt. 1) then
;                  base_index(0,zz,yy,xx)= 1.
;               else
; ;                 if(zz.gt.mdims(1)/2) then
; ;                  base_index(time,:,yy,xx)=base_index@_FillValue 
; ;                  top_index(time,:,yy,xx)=top_index@_FillValue 
; ;                  zz=mdims(1)-1
; ;                 else
;                   base_index(0,zz-1,yy,xx) = 1.
; ;                 end if
;               end if

;                   do while(index_qt(0,zz,yy,xx).gt.0.5 .and. zz.lt.mdims(1)-1)
;                     zz=zz+1
;                   end do
;                   top_index(0,zz-1,yy,xx) = 1.

; ;                 zz =mdims(1)-1

; ;               end if
; ;              end do; zz
;               temp = 0.

;            end do;temp
;         end do ;;yy
;      end do ;;xx

;     CTT=dim_avg_n(tc*top_index,1)
;     CBH=dim_avg_n(hgt(:,0:mdims(1)-1,:,:)*base_index,1)
;     CDP=dim_avg_n(hgt(:,1:mdims(1),:,:)*top_index,1)-CBH
;     CTT@_FillValue=-999.
;     CBH@_FillValue=-999.
;     CDP@_FillValue=-999.

; LWP MC 
    ; lwp=index
    ; lwp=dim_sum_n(qw*dz,1)
    ; delete(qw)

; LWC values
    lwc_gmc=dim_avg_n(index_hagl*lw,1)*1000.
    ; lwc_gmc2=dim_avg_n(index_hagl2*lw,1)*1000.
    lwc_amc=dim_avg_n(index_hasl*lw,1)*1000.

    iwc_gmc=dim_avg_n(index_hagl*qice,1)*1000.
    ; iwc_gmc2=dim_avg_n(index_hagl2*qice,1)*1000.
    iwc_amc=dim_avg_n(index_hasl*qice,1)*1000.

    lwc_gmc_crit=where(lwc_gmc.gt. 0.009999 , 1,0)
    lwc_gmc_crit@_FillValue=-1
    ; lwc_gmc2_crit=where(lwc_gmc2.gt. 0.009999 , 1,0)
    ; lwc_gmc2_crit@_FillValue=-1
    lwc_amc_crit=where(lwc_amc.gt. 0.009999 , 1,0)
    lwc_amc_crit@_FillValue=-1

; LWR (Qw/Qt)

    qt_gs_int=dim_sum_n(qt*rho*dz*index_hagl,1)
    ; qt_gs_int2=dim_sum_n(qt*rho*dz*index_hagl2,1)
    qt_as_int=dim_sum_n(qt*rho*dz*index_hasl,1)

    lw_gs=dim_sum_n(lw*rho*dz*index_hagl,1)
    ; lw_gs2=dim_sum_n(lw*rho*dz*index_hagl2,1)
    lw_as=dim_sum_n(lw*rho*dz*index_hasl,1)

    qt_gs_int=where(qt_gs_int.lt.1.e-5,-999.0,qt_gs_int)
    qt_gs_int@_FillValue=-999.0
    qwqt_gmc=lw_gs/qt_gs_int

    ; qt_gs_int2=where(qt_gs_int2.lt.1.e-5,-999.0,qt_gs_int2)
    ; qt_gs_int2@_FillValue=-999.0
    ; qwqt_gmc2=lw_gs2/qt_gs_int2
   
    cloudness_gs=where(qt_gs_int.ge.1.e-5,1.,-999.)
    cloudness_gs@_FillValue=-999.0

    ; cloudness_gs2=where(qt_gs_int2.ge.1.e-5,1.,-999.)
    ; cloudness_gs2@_FillValue=-999.0

    qt_as_int=where(qt_as_int.lt.1.e-5,-999.0,qt_as_int)
    qt_as_int@_FillValue=-999.0
    qwqt_amc=lw_as/qt_as_int

    cloudness_as=where(qt_as_int.ge.1.e-5,1.,-999.)
    cloudness_as@_FillValue=-999.0

    delete(rho)
    delete(lw)
;    delete(qt)
    delete(lw_gs)
    ; delete(lw_gs2)
    delete(lw_as)
    delete(qt_gs_int)
    ; delete(qt_gs_int2)
    delete(qt_as_int)

; T values and MC
    tc_gmc=dim_avg_n(index_hagl*tc,1)
    ; tc_gmc2=dim_avg_n(index_hagl2*tc,1)
    tc_amc=dim_avg_n(index_hasl*tc,1)

    tc_gmc_crit=where(tc_gmc.gt. -17.9999 .and.tc_gmc.lt. -6.0001,1,0)
    tc_gmc_crit@_FillValue=-1

    ; tc_gmc2_crit=where(tc_gmc2.gt. -17.9999 .and.tc_gmc2.lt. -6.0001,1,0)
    ; tc_gmc2_crit@_FillValue=-1

    tc_amc_crit=where(tc_amc.gt. -17.9999 .and.tc_amc.lt. -6.0001,1,0)
    tc_amc_crit@_FillValue=-1


    slw_gmc_crit=where(lwc_gmc.gt. 0.009999 .and. tc_gmc.gt. -17.9999 .and.tc_gmc.lt. -6.0001, 1,0)
    slw_gmc_crit@_FillValue=-1
    ; slw_gmc2_crit=where(lwc_gmc2.gt. 0.009999 .and. tc_gmc2.gt. -17.9999 .and.tc_gmc2.lt. -6.0001, 1,0)
    ; slw_gmc2_crit@_FillValue=-1
    slw_amc_crit=where(lwc_amc.gt. 0.009999 .and. tc_amc.gt. -17.9999 .and.tc_amc.lt. -6.0001, 1,0)
    slw_amc_crit@_FillValue=-1

    delete(tc)

; wind and instability
    uvmet=wrf_user_getvar(a,"uvmet",-1)
    ua=uvmet(0,:,:,:,:)
    va=uvmet(1,:,:,:,:)

    delete(uvmet)
    
    ; u_250mb=dim_avg_n(ua*index_250mb,1)
    ; v_250mb=dim_avg_n(va*index_250mb,1)
    ; u_250mb@_FillValue=-999.
    ; v_250mb@_FillValue=-999.

    ; u_500mb=dim_avg_n(ua*index_500mb,1)
    ; v_500mb=dim_avg_n(va*index_500mb,1)
    ; u_500mb@_FillValue=-999.
    ; v_500mb@_FillValue=-999.

    u_700mb=dim_avg_n(ua*index_700mb,1)
    v_700mb=dim_avg_n(va*index_700mb,1)
    u_700mb@_FillValue=-999.
    v_700mb@_FillValue=-999.

    ; u_850mb=dim_avg_n(ua*index_850mb,1)
    ; v_850mb=dim_avg_n(va*index_850mb,1)
    ; u_850mb@_FillValue=-999.
    ; v_850mb@_FillValue=-999.

    uaz=hgt
    uaz=0.
    vaz=uaz
  
    uaz(:,0,:,:)=0.
    vaz(:,0,:,:)=0.

    do k=1,mdims(1)-1
     uaz(:,k,:,:)=0.5*(ua(:,k,:,:)+ua(:,k-1,:,:))
     vaz(:,k,:,:)=0.5*(va(:,k,:,:)+va(:,k-1,:,:))
    end do
   
    u_gdc=dim_avg_n(index_hagl*ua,1)
    ; u_gdc2=dim_avg_n(index_hagl2*ua,1)
    u_adc=dim_avg_n(index_hasl*ua,1)

    v_gdc=dim_avg_n(index_hagl*va,1)
    ; v_gdc2=dim_avg_n(index_hagl2*va,1)
    v_adc=dim_avg_n(index_hasl*va,1)

    ; th=tk*(100000./p)^0.286
    ; bn2_full=th

    ; tsk=b->T2
    ; psfc=a->P(:,0,:,:)

    ; thz=hgt

    ; thz(:,0,:,:)=tsk*(100000./psfc)^0.286

    ; do k=1,mdims(1)-1
    ;  thz(:,k,:,:)=(th(:,k,:,:)+th(:,k-1,:,:))*0.5
    ; end do

; BN2 ;undefined without a target range
;   do k=0,mdims(1)-1
;    bn2_full(:,k,:,:)=g/th(:,k,:,:)*(thz(:,k+1,:,:)-thz(:,k,:,:))/dz(:,k,:,:)
;   end do
   
;     bn2=dim_avg_n(index_hagl*bn2_full,1)
	
; 	; copy for all 3 ranges
; 	; srr peak height: 2800m
; 	; brr: 2500m
; 	; uin: 3500m
; 	; uintas
; 	fr_UIN = ter
; 	fr_UIN = 0.
; 	fr_UIN@_FillValue=-999
; 	h_local_UIN=height_agl
; 	h_local_UIN=0.
; 	do k=0,mdims(1)-1
; 		h_local_UIN(:,k,:,:)=-(ter-3500.) ; GET MTN HGT
; 	end do
; 	index_huin=where(height_agl.lt.h_local_UIN,1.,-999.)
; 	index_huin@_FillValue=-999
; 	u_uin=dim_avg_n(index_huin*ua,1)
; 	v_uin=dim_avg_n(index_huin*va,1)
; 	bn2_uin=dim_avg_n(index_huin*bn2_full,1)
; 	bn2_uin=where(bn2_uin.eq.0.,-999.,bn2_uin)
; 	bn2_uin@_FillValue=-999.
; 	fr_UIN=(u_uin*cos(phi_UIN)+v_uin*sin(phi_UIN))/(abs(bn2_uin))^0.5/h_local_UIN(:,0,:,:)
; 	fr_UIN=where(fr_UIN.lt.10.,fr_UIN,10.)
	
; 	; srr
; 	fr_SRR = ter
; 	fr_SRR = 0.
; 	fr_SRR@_FillValue=-999
; 	h_local_SRR=height_agl
; 	h_local_SRR=0.
; 	do k=0,mdims(1)-1
; 		h_local_SRR(:,k,:,:)=-(ter-2800.) ; GET MTN HGT
; 	end do
; 	index_hsrr=where(height_agl.lt.h_local_SRR,1.,-999.)
; 	index_hsrr@_FillValue=-999
; 	u_srr=dim_avg_n(index_hsrr*ua,1)
; 	v_srr=dim_avg_n(index_hsrr*va,1)
; 	bn2_srr=dim_avg_n(index_hsrr*bn2_full,1)
; 	bn2_srr=where(bn2_srr.eq.0.,-999.,bn2_srr)
; 	bn2_srr@_FillValue=-999.
; 	fr_SRR=(u_srr*cos(phi_SRR)+v_srr*sin(phi_SRR))/(abs(bn2_srr))^0.5/h_local_SRR(:,0,:,:)
; 	fr_SRR=where(fr_SRR.lt.10.,fr_SRR,10.)
	
; 	; brr
; 	fr_BRR = ter
; 	fr_BRR = 0.
; 	fr_BRR@_FillValue=-999
; 	h_local_BRR=height_agl
; 	h_local_BRR=0.
; 	do k=0,mdims(1)-1
; 		h_local_BRR(:,k,:,:)=-(ter-2500.) ; GET MTN HGT
; 	end do
; 	index_hbrr=where(height_agl.lt.h_local_BRR,1.,-999.)
; 	index_hbrr@_FillValue=-999
; 	u_brr=dim_avg_n(index_hbrr*ua,1)
; 	v_brr=dim_avg_n(index_hbrr*va,1)
; 	bn2_brr=dim_avg_n(index_hbrr*bn2_full,1)
; 	bn2_brr=where(bn2_brr.eq.0.,-999.,bn2_brr)
; 	bn2_brr@_FillValue=-999.
; 	fr_BRR=(u_brr*cos(phi_BRR)+v_brr*sin(phi_BRR))/(abs(bn2_brr))^0.5/h_local_BRR(:,0,:,:)
; 	fr_BRR=where(fr_BRR.lt.10.,fr_BRR,10.)
	
; Delete height variables
    ; delete(tsk)
    delete(p)
    ; delete(psfc)
    ; delete(th)
    ; delete(thz)
    ; delete(bn2_full)
    delete(ua)
    delete(va)
    delete(uaz)
    delete(vaz)
    delete(height)
    delete(height_agl)
    delete(dz)
    delete(index_hagl)
    ; delete(index_hagl2)
    delete(index_hasl)

    
    outcdf=addfile(cf, "c")

    setfileoption(outcdf,"DefineMode",True)

    dimNames = (/"Time", "south_north", "west_east"/)
    ; dimSizes = (/ 1 ,    39,  82 /)
    dimSizes = (/ 1 ,    131,  121 /)
    dimUnlim = (/ True , False, False/)
    filedimdef(outcdf, dimNames, dimSizes, dimUnlim)
    var_names = (/ "AS_LWC", "AS_LWC_CRIT", "AS_Tc", "AS_Tc_CRIT", "AS_IWC", "AS_SLW_CRIT", "AS_U",  "AS_V",  "GS_LWC", "GS_LWC_CRIT", "GS_Tc", "GS_Tc_CRIT", "GS_IWC", "GS_SLW_CRIT", "GS_U",  "GS_V", "Tc_700MB", "U_700MB", "V_700MB", "Z_700MB"/)
    var_types = (/ "float",  "integer",     "float", "integer",    "float",  "integer",      "float", "float", "float",  "integer",     "float", "integer",   "float",  "integer",     "float", "foat", "float",    "float",   "float",   "float"/)

    ; "GS_LWC2", "GS_LWC2_CRIT", "GS_Tc2", "GS_Tc2_CRIT", "GS_IWC2", "GS_SLW2_CRIT", "GS_U2",  "GS_V2",  "Tc_250MB", "U_250MB", "V_250MB", "Z_250MB", "Tc_500MB", "U_500MB", "V_500MB", "Z_500MB", , "Tc_850MB", "U_850MB", "V_850MB", "Z_850MB"/)
    ; "float",  "integer",      "float",  "integer",     "float",   "integer",      "float",  "float",    "float",   "float",   "float",   "float",   "float",   "float",   "float",   "float",   ,   "float",    "float",   "float",   "float"/)
    filevardef(outcdf, var_names, var_types, dimNames)
    outcdf->Time=Time
    outcdf->AS_LWC=(/lwc_amc/)
    outcdf->AS_LWC_CRIT=(/lwc_amc_crit/)
    outcdf->AS_Tc=(/tc_amc/)
    outcdf->AS_Tc_CRIT=(/tc_amc_crit/)
    outcdf->AS_IWC=(/iwc_amc/)
    outcdf->AS_SLW_CRIT=(/slw_amc_crit/)
    outcdf->AS_U=(/u_adc/)
    outcdf->AS_V=(/v_adc/)
    outcdf->GS_LWC=(/lwc_gmc/)
    outcdf->GS_LWC_CRIT=(/lwc_gmc_crit/)
    outcdf->GS_Tc=(/tc_gmc/)
    outcdf->GS_Tc_CRIT=(/tc_gmc_crit/)
    outcdf->GS_IWC=(/iwc_gmc/)
    outcdf->GS_SLW_CRIT=(/slw_gmc_crit/)
    outcdf->GS_U=(/u_gdc/)
    outcdf->GS_V=(/v_gdc/)
    ; outcdf->GS_LWC2=(/lwc_gmc2/)
    ; outcdf->GS_LWC2_CRIT=(/lwc_gmc2_crit/)
    ; outcdf->GS_Tc2=(/tc_gmc2/)
    ; outcdf->GS_Tc2_CRIT=(/tc_gmc2_crit/)
    ; outcdf->GS_IWC2=(/iwc_gmc2/)
    ; outcdf->GS_SLW2_CRIT=(/slw_gmc2_crit/)
    ; outcdf->GS_U2=(/u_gdc2/)
    ; outcdf->GS_V2=(/v_gdc2/)
    ; outcdf->Tc_250MB=(/tc_250mb/)
    ; outcdf->U_250MB=(/u_250mb/)
    ; outcdf->V_250MB=(/v_250mb/)
    ; outcdf->Z_250MB=(/z_250mb/)
    ; outcdf->Tc_500MB=(/tc_500mb/)
    ; outcdf->U_500MB=(/u_500mb/)
    ; outcdf->V_500MB=(/v_500mb/)
    ; outcdf->Z_500MB=(/z_500mb/)
    outcdf->Tc_700MB=(/tc_700mb/)
    outcdf->U_700MB=(/u_700mb/)
    outcdf->V_700MB=(/v_700mb/)
    outcdf->Z_700MB=(/z_700mb/)
    ; outcdf->Tc_850MB=(/tc_850mb/)
    ; outcdf->U_850MB=(/u_850mb/)
    ; outcdf->V_850MB=(/v_850mb/)
    ; outcdf->Z_850MB=(/z_850mb/)
  end do
end
