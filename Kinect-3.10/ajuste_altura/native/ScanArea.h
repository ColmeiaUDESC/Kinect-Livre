// Convex four-corner selection in normalized, top-down depth image coordinates.
#ifndef SCAN_AREA_INCLUDED
#define SCAN_AREA_INCLUDED
#include <cmath>
#include <fstream>
#include <stdexcept>
#include <vector>
struct ScanArea
{
    double p[4][2];
    void load(const std::string& path)
    {
        std::ifstream input(path.c_str());
        for(int i=0;i<4;++i) for(int j=0;j<2;++j)
            if(!(input>>p[i][j])||!std::isfinite(p[i][j])||p[i][j]<0||p[i][j]>1)
                throw std::runtime_error("Invalid scan area coordinates");
        double sign=0,area=0;
        for(int i=0;i<4;++i)
        {
            const int j=(i+1)%4,k=(i+2)%4;
            const double cross=(p[j][0]-p[i][0])*(p[k][1]-p[j][1])-(p[j][1]-p[i][1])*(p[k][0]-p[j][0]);
            if(std::abs(cross)<1e-6||(sign!=0&&cross*sign<=0))
                throw std::runtime_error("Scan area must have four convex corners in perimeter order");
            sign=cross;
            area+=p[i][0]*p[j][1]-p[j][0]*p[i][1];
        }
        if(std::abs(area)<0.01) throw std::runtime_error("Scan area is too small");
    }
    bool contains(double x,double y) const
    {
        double sign=0;
        for(int i=0;i<4;++i)
        {
            int j=(i+1)%4;
            double c=(p[j][0]-p[i][0])*(y-p[i][1])-(p[j][1]-p[i][1])*(x-p[i][0]);
            if(std::abs(c)<1e-12) continue;
            if(sign!=0&&sign*c<0) return false;
            sign=c;
        }
        return true;
    }
    std::vector<unsigned char> mask(unsigned int w,unsigned int h) const
    {
        std::vector<unsigned char> result(w*h);
        for(unsigned int y=0;y<h;++y) for(unsigned int x=0;x<w;++x)
            result[y*w+x]=contains((x+0.5)/w,1.0-(y+0.5)/h);
        return result;
    }
};
#endif
