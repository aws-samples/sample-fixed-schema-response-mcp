"""
Model connector interfaces and implementations for the Fixed Schema Response MCP Server.

This module provides abstract interfaces and concrete implementations for connecting
to various language model providers.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Tuple

try:
    import openai
except ImportError:
    openai = None

from fixed_schema_mcp_server.model.exceptions import (
    ModelError,
    ModelConnectionError,
    ModelResponseError,
    ModelTimeoutError,
    ModelRateLimitError,
    ModelAuthenticationError,
)
l

name__)


class M):
    """
    ors.
    
    This class defines the interface that all model connectors must implement.
    Model connectors are responsible for communicatingAPIs
    ands API.
    """
    
    @abstractmethod
    async d
        """
         model.
        
        Args:
            prompt: The prompt to send to the model
            
            
        Returns:
            ing
            
        Raises:
            ModelConnectionError: If there is an error connecting to the model API
            ModelResponseError: If there is an error processie
            ModelTimeoutError: If the model request times out
            ModelRateLimitError: If the model API rate limit is exceeded
           r
        """
        pass
    
    @abstractmethod
    def getny]:
        """
        he model.
        
        Returns:
           ameters
        """
    ass
    
    @abstractmethod
    def updone:
        """
        
        
        Args:
           te
        """
        pass
    
    @abstractmethod
    def get> str:
        """
        r.
        
        Returns:
           pic")
        """
    ss
    
    @abstractmethod
    def get:
        """
        used.
        
        Returns:
           ")
        """
    s
    
    @abstractmethod
    async d
        """
        ble.
        
        Returns:
            A tuple containing:
            - A boolean indicating whether the API is healthy
           ealthy
        """
    
    
    def mery]:
        """
        s.
        
        Args:
            defaults
            
        Returns:
           s
        """
        merged = self.opy()
        if parameters:
            merged.uprs)
ged


class O:
    """
    AI API.
    
    Thi.
    
    
    def __i
        self,
        tr,
        model",
        default_parameters: Optional[Di = None,
        pool_size: int = 5,
        max_pool_size: int = 10
    ):
        """
        Initialize the OpenAI model cor.
        
        Args:
            api_key: The y
            model_name: The nam
            default_parameters: Optiodel
            pool_size: The minimum n
         e pool
        """
        self._api_key = api_ey
    
        self._default_parameters = d
           .7,
            "top_p": 1.0,
        1000,
            "fr
            "presence_penalty": 0.0,
        }
        self
        self._max_pool_sisize
        self._connection_pool = None
        self._setup_connection_pool()
    
    def _setup_connection_pool(self) ->one:
        """
        Set up the connection pool.
        
        Raises:
            ModelConnectionError: If thtion pool
        """
        try:
            self._conne
             nt,
    health,
                close_connection=self._close_client,
           e,
                max_size=self._max_pool_size,
        minutes
             nute
            )
            logger.info(f"OpenAI connection pool initialized for model
        exce
            rais
                f"Failed to initialize OpenAI (e)}",
            nai",
               cause=e
            )
    
    async def _create_client(self):
        """
        Create a new OpenAI client.
        
        Returns:
            A new OpenAI client
        
        Raises:
        nt
        """
        try:
            import openai
            client = openai.AsyncOpenAI(api_key=self._api_key)
            logger.debug(f"Crea)
            rt
        excer:
            raise ModelConnectionError(
                "OpenAI package not installed. Install it with 'pip install openai'.",
            i"
            )
        exce
            raise ModelConnectionError(
                f"Failed to cr
                provider="openai",
                cause=e
            )
    
    async def _check_client_healthool:
        """
        Checkealthy.
        
        Args:
            client: The
            
        Returns:
            True if the client is healthyerwise
        """
        try:
            # Make a simple models.list request to css
            ast()
            return True
        except Exception as e:
            logger.warning(f"OpenAI client )
            return False
    
    async def _close_client:
        """
        Close an OpenAI client.
        
        Args:
            client: The OpenAI client to close
        """
        # OpenAI clients don't need explicit closing, but we'll log it
        logger.debug("Close")
    
    async def start(self) -> None:
    ."""
        if self._connection_pool:
           l.start()
    
    asyne:
        """Stop "
        if self._connection_pool:
           
    
    > str:
        """
        GenAI model.
        
        gs:
            pl
            parameters: Optional model parameterfaults
           
        Returns:
    
            
        Rai
            ModelConnectionError: If there  API
        e
            Modet
            ModelRateLimitError
           
        """
    on_pool:
            self._setup_connection_p)
           )
        
        
        client =e
        
        try
            # Acquire a client ol
    ()
            
           ll
            response = await client.chat.completions.create(
        
                }],
                **merged_params
            )
            
           
                raise ModelR
            
            # Release the client bacpool
            await self._connection_
            client = None  # Preventock
           
            .content
            
        except openai.RateLimitError as e:
            # Mark the clienthealthy
            if client:
                await self._connection_pool.mark_unhealthy(client)   ()get_statsion_pool.elf._connect return s        
   
    itialized"}l not inection pooConn "r":turn {"erro          ren_pool:
  nnectiof._co if not sel    ""
   
        "ion poolhe connectout ts abtisticaining staontry c A dictiona           turns:
        Re  
   .
   ion pool connecthes about tsticGet stati   
     "   ""ny]:
     ct[str, Aelf) -> Distats(stion_pool_connec  def get_    
  }"
ed: {str(e)ailk fth checI healAPAI enlse, f"Op   return Fa        ion as e:
 cept Except
        ex, Nonen True      retur       
          pool"
 n the ons ionnectihy calto heFalse, "N  return       :
        "]nections_conealthyats["unh stns"] ==nectiotal_constats["to== 0 or ections"] "total_connats[st  if         
  lthy hea not, the API isonsthy connectio healthere are n   # If      
               )
 stats(on_pool.get_onnecti = self._c stats        ats
    pool stion Get connect      #    :
  
        try        
se, str(e)Falreturn                 
ror as e:lErModept   exce          tart()
ion_pool.sonnect._c await self              n_pool()
 ectiotup_conn  self._se         ry:
        t       _pool:
  ectionf._connf not sel   i
        """
     ot healthy nthe API is if sage mes errorh anng witstritional n op     - A       
thyI is healhe APher tg whet indicatinan   - A boole:
         ngnintaiple co A tu           eturns:
    R 
         
  cessible.thy and acPI is healI Ahe OpenA if t       Check   """
   :
   l[str]]ionale[bool, Optself) -> Tuph_check(f healtsync de    
    ael_name
modeturn self._"
        r   ""   4")
  "gpt-g.,  model (e.f theThe name o        
      Returns:    
   
       ing used. model bee OpenAI of thameGet the n   ""
        "    -> str:
  elf)ame(s_ndel  def get_mo  
  nai"
  "ope     return    """
   i"
     g "openastrinThe           rns:
       Retu
         der.
   model proviname of the   Get the ""
       ":
      self) -> strer_name(videf get_pro
    d
    parameters)s.update(rameter_default_pa       self."""
       ate
  s to updarameterters: The p   parame             Args:
          
  ameters.
el pare OpenAI modthte     Upda""
         "
   -> None:ny])  A[str,ctrameters: Dipaters(self, _parameate   def upd
 y()
    meters.coplt_paraaulf._defreturn se"
           ""ers
     etault paramnary of def A dictio
           s:rn      Retu    
  del.
    he OpenAI mos for tter parameltefaut the d     Ge
   """        tr, Any]:
> Dict[sf) -rs(selmeterat_default_page 
    def e}")
   t to pool: {ng clieneleasi rError.error(f"  logger                  as e:
 Exception    except         ient)
    lease(cln_pool.reectiolf._connait se       aw       :
      ry           t     client:
  if   ed
        eady releast alr wasn'e pool if it thack toent b the cliRelease   # :
         lly      finas as-is
  e ModelErrore-rais Rraise  #        )
           e
         use=       ca            (e)}",
 penAI: {strfrom Osponse ing rer generat"Erro f          
         ponseError(ModelRes      raise        rrors
   ng ModelEpi-wrapid re  # AvoelError):e, Modstance(sin    if not i
        nseErrorespoModelRion to a exceptther rt any o # Conve      
                    )
              cause=e
               ",
    ="openaier      provid              
",)}str(e error: {API"OpenAI  f                 or(
  tionErrecConnraise Model            ror):
    ai.APIErance(e, open and isinst openai          if 
           
  lly blockn finae int releasvene  # Pre client = No            nt)
   lie(cunhealthymark_tion_pool.onnecait self._c        aw    t:
    clienf     i     ror
   er any other  forthyt as unhealien cl # Mark the          as e:
  onExceptit        excep
  )        ut")
   timeorams.get("=merged_patimeout               ed out",
 I timnAI APOpeest to    "Requ          or(
   rrdelTimeoutEraise Mo                 
       block
 e in finallynt releasne  # Preveient = No     cl      ient)
     lthy(clmark_unheaon_pool.tilf._connect se        awai
        nt: clie        if
    lthy unheaient asark the cl  # M
          rror as e:TimeoutEasyncio.ept  exc  )
              nai"
   vider="ope      pro
           str(e),          r(
     ronErhenticatioModelAut      raise            
  ock
     blly n final release i  # Preventoneent = N        cli
        lthy(client)mark_unheapool.tion_self._connec     await            ent:
 cli         ifhy
   nhealt as uclientark the      # M   :
    Error as etion.Authenticapenait o  excep    
        )ter
      ter=retry_af_af  retry            penai",
  "orovider=     p           str(e),
            rror(
    tEdelRateLimiise Mo ra
           aftery_r = e.retr retry_afte           :
    _after')r(e, 'retrytthasa   if          e
r = Nonfte retry_a            
   ck
        lly blo in finaaserele# Prevent e   = Nonent      cli
       